from unittest import mock

import jwt

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.models import LogEntry
from django.db import connection
from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice

from bluebottle.auth.middleware import HIJACK_OTP_DEVICE_SESSION_KEY, OTPMiddleware, SlidingJwtTokenMiddleware
from bluebottle.auth.permissions import can_hijack
from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.members import signals
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import ApiClient, BluebottleAdminTestCase, BluebottleTestCase


class HijackPermissionTest(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        self.staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        self.member = BlueBottleUserFactory.create(is_staff=False, is_superuser=False)
        self.other_superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        self.inactive_staff = BlueBottleUserFactory.create(
            is_staff=True, is_superuser=False, is_active=False
        )
        for user in (self.superuser, self.staff, self.other_superuser):
            user.is_verified = lambda: True

    def test_superuser_can_hijack_staff(self):
        self.assertTrue(can_hijack(hijacker=self.superuser, hijacked=self.staff))

    def test_unverified_superuser_cannot_hijack(self):
        self.superuser.is_verified = lambda: False
        self.assertFalse(can_hijack(hijacker=self.superuser, hijacked=self.staff))

    def test_superuser_without_otp_state_cannot_hijack(self):
        del self.superuser.is_verified
        self.assertFalse(can_hijack(hijacker=self.superuser, hijacked=self.staff))

    def test_cannot_hijack_member(self):
        self.assertFalse(can_hijack(hijacker=self.superuser, hijacked=self.member))

    def test_cannot_hijack_superuser(self):
        self.assertFalse(can_hijack(hijacker=self.superuser, hijacked=self.other_superuser))

    def test_cannot_hijack_inactive_staff(self):
        self.assertFalse(can_hijack(hijacker=self.superuser, hijacked=self.inactive_staff))

    def test_staff_cannot_hijack(self):
        self.assertFalse(can_hijack(hijacker=self.staff, hijacked=self.member))
        self.assertFalse(can_hijack(hijacker=self.staff, hijacked=self.superuser))

    def test_cannot_hijack_self(self):
        self.assertFalse(can_hijack(hijacker=self.superuser, hijacked=self.superuser))


class MemberHijackAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        self.staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        self.member = BlueBottleUserFactory.create(is_staff=False)
        self.other_superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        self.acquire_url = reverse('hijack:acquire')
        self.release_url = reverse('hijack:release')

    def test_superuser_acquires_and_releases_staff(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            self.acquire_url,
            {'user_pk': str(self.staff.pk)},
            format='multipart',
        )
        self.assertEqual(response.status_code, 302)

        index = self.client.get(reverse('admin:index'))
        self.assertEqual(index.status_code, 200)
        self.assertContains(index, 'djhj')
        self.assertContains(index, 'Stop impersonating')
        self.assertNotContains(index, 'hide warning')
        self.assertNotContains(index, 'Hide notification')

        response = self.client.post(self.release_url, {}, format='multipart')
        self.assertEqual(response.status_code, 302)

        index = self.client.get(reverse('admin:index'))
        self.assertEqual(index.status_code, 200)
        self.assertNotContains(index, 'djhj')

    def test_cannot_acquire_member(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            self.acquire_url,
            {'user_pk': str(self.member.pk)},
            format='multipart',
        )
        self.assertEqual(response.status_code, 403)

    def test_cannot_acquire_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.post(
            self.acquire_url,
            {'user_pk': str(self.other_superuser.pk)},
            format='multipart',
        )
        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_acquire(self):
        other_staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        self.client.force_login(self.staff_member)
        response = self.client.post(
            self.acquire_url,
            {'user_pk': str(other_staff.pk)},
            format='multipart',
        )
        self.assertEqual(response.status_code, 403)

    def test_release_restores_otp_device(self):
        device = TOTPDevice.objects.create(
            user=self.superuser, name='default', confirmed=True
        )
        self.client.force_login(self.superuser)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()

        self.client.post(
            self.acquire_url,
            {'user_pk': str(self.staff.pk)},
            format='multipart',
        )
        self.assertEqual(
            self.client.session.get(HIJACK_OTP_DEVICE_SESSION_KEY),
            device.persistent_id,
        )

        response = self.client.post(self.release_url, {}, format='multipart')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session.get(DEVICE_ID_SESSION_KEY),
            device.persistent_id,
        )

        with override_settings(DISABLE_TWO_FACTOR=False):
            index = self.client.get(reverse('admin:index'))
            self.assertEqual(index.status_code, 200)
            self.assertNotContains(index, 'djhj')


class HijackOtpMiddlewareTest(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.request_factory = RequestFactory()

    def _verify_hijacked(self, hijacker, device=None):
        staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        staff.is_hijacked = True
        request = self.request_factory.get('/en/admin/')
        request.session = {'hijack_history': [str(hijacker.pk)]}
        if device:
            request.session[HIJACK_OTP_DEVICE_SESSION_KEY] = device.persistent_id

        middleware = OTPMiddleware(get_response=lambda r: None)
        with override_settings(DISABLE_TWO_FACTOR=False):
            return middleware._verify_user(request, staff)

    def test_hijacked_user_is_verified_with_hijackers_device(self):
        superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        device = TOTPDevice.objects.create(user=superuser, name='default', confirmed=True)

        user = self._verify_hijacked(superuser, device)

        self.assertTrue(user.is_verified())
        self.assertEqual(user.otp_device, device)

    def test_hijacked_user_without_device_is_not_verified(self):
        superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)

        user = self._verify_hijacked(superuser)

        self.assertFalse(user.is_verified())

    def test_hijacked_user_with_someone_elses_device_is_not_verified(self):
        superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        other = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        device = TOTPDevice.objects.create(user=other, name='default', confirmed=True)

        user = self._verify_hijacked(superuser, device)

        self.assertFalse(user.is_verified())

    def test_hijacked_user_with_unconfirmed_device_is_not_verified(self):
        superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        device = TOTPDevice.objects.create(user=superuser, name='default', confirmed=False)

        user = self._verify_hijacked(superuser, device)

        self.assertFalse(user.is_verified())

    def test_unhijacked_user_without_device_is_not_verified(self):
        staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        request = self.request_factory.get('/en/admin/')
        request.session = {}

        middleware = OTPMiddleware(get_response=lambda r: None)
        with override_settings(DISABLE_TWO_FACTOR=False):
            user = middleware._verify_user(request, staff)

        self.assertFalse(user.is_verified())


class HijackSecurityTest(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        self.staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        self.acquire_url = reverse('hijack:acquire')
        self.release_url = reverse('hijack:release')

    def acquire(self, user=None, client=None, **data):
        client = client or self.client
        return client.post(
            self.acquire_url,
            {'user_pk': str((user or self.staff).pk), **data},
            format='multipart',
        )

    def release(self, **data):
        return self.client.post(self.release_url, data, format='multipart')

    def login_with_otp(self, user):
        device = TOTPDevice.objects.create(user=user, name='default', confirmed=True)
        self.client.force_login(user)
        session = self.client.session
        session[DEVICE_ID_SESSION_KEY] = device.persistent_id
        session.save()
        return device

    def current_user_pk(self):
        return self.client.session.get('_auth_user_id')

    def test_anonymous_cannot_acquire(self):
        response = self.acquire()
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])
        self.assertIsNone(self.current_user_pk())

    def test_inactive_superuser_cannot_acquire(self):
        self.client.force_login(self.superuser)
        self.superuser.is_active = False
        self.superuser.save()

        response = self.acquire()
        self.assertNotEqual(self.current_user_pk(), str(self.staff.pk))
        self.assertIn(response.status_code, (302, 403))

    def test_cannot_acquire_self(self):
        self.client.force_login(self.superuser)
        self.assertEqual(self.acquire(self.superuser).status_code, 403)

    def test_cannot_acquire_inactive_staff(self):
        self.staff.is_active = False
        self.staff.save()
        self.client.force_login(self.superuser)
        self.assertEqual(self.acquire().status_code, 403)

    def test_cannot_acquire_unknown_user(self):
        self.client.force_login(self.superuser)
        response = self.client.post(self.acquire_url, {'user_pk': '999999'}, format='multipart')
        self.assertEqual(response.status_code, 404)

    def test_acquire_requires_user_pk(self):
        self.client.force_login(self.superuser)
        response = self.client.post(self.acquire_url, {}, format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_get_does_not_acquire(self):
        self.client.force_login(self.superuser)
        self.client.get(self.acquire_url, {'user_pk': str(self.staff.pk)})
        self.assertEqual(self.current_user_pk(), str(self.superuser.pk))

    def test_release_when_not_hijacked_is_forbidden(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.release().status_code, 403)
        self.assertEqual(self.current_user_pk(), str(self.staff.pk))

    def test_acquire_without_otp_verification_is_forbidden(self):
        with override_settings(DISABLE_TWO_FACTOR=False):
            self.client.force_login(self.superuser)
            response = self.acquire()

            self.assertEqual(response.status_code, 403)
            self.assertEqual(self.current_user_pk(), str(self.superuser.pk))

    def test_acquire_with_otp_verification_gives_admin_access(self):
        with override_settings(DISABLE_TWO_FACTOR=False):
            self.login_with_otp(self.superuser)
            self.assertEqual(self.acquire().status_code, 302)
            self.assertEqual(self.current_user_pk(), str(self.staff.pk))

            index = self.client.get(reverse('admin:index'))
            self.assertEqual(index.status_code, 200)
            self.assertContains(index, 'Stop impersonating')

    def test_hijacked_session_without_device_has_no_admin_access(self):
        with override_settings(DISABLE_TWO_FACTOR=False):
            self.login_with_otp(self.superuser)
            self.acquire()
            session = self.client.session
            session.pop(HIJACK_OTP_DEVICE_SESSION_KEY, None)
            session.pop(DEVICE_ID_SESSION_KEY, None)
            session.save()

            index = self.client.get(reverse('admin:index'))
            self.assertNotEqual(index.status_code, 200)

    def test_session_key_rotates(self):
        self.client.force_login(self.superuser)
        before = self.client.session.session_key

        response = self.acquire()
        self.assertEqual(response.status_code, 302, response.content[:300])
        hijacked = self.client.session.session_key
        self.assertNotEqual(before, hijacked)

        self.release()
        self.assertNotEqual(hijacked, self.client.session.session_key)
        self.assertEqual(self.current_user_pk(), str(self.superuser.pk))

    def test_last_login_not_updated(self):
        last_login = self.staff.last_login
        self.client.force_login(self.superuser)
        self.acquire()
        self.release()

        self.staff.refresh_from_db()
        self.assertEqual(self.staff.last_login, last_login)

    def test_logout_while_hijacked_ends_both_sessions(self):
        self.client.force_login(self.superuser)
        self.acquire()

        self.client.post(reverse('admin:logout'), format='multipart')

        self.assertIsNone(self.current_user_pk())
        self.assertNotIn('hijack_history', self.client.session)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)

    def test_hijacked_staff_gets_no_superuser_permissions(self):
        url = reverse('admin:members_member_changelist')
        self.client.force_login(self.superuser)
        self.assertEqual(self.client.get(url).status_code, 200)

        self.acquire()

        self.assertEqual(self.client.get(url).status_code, 403)

    def test_nested_hijack_is_forbidden(self):
        other_staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        self.client.force_login(self.superuser)
        self.acquire()

        self.assertEqual(self.acquire(other_staff).status_code, 403)
        self.assertEqual(self.current_user_pk(), str(self.staff.pk))

    def test_api_only_sees_hijacked_user(self):
        self.client.force_login(self.superuser)
        self.acquire()

        response = self.client.get(reverse('user-current'))

        self.assertEqual(response.json()['id'], self.staff.pk)
        self.assertNotIn('Refresh-Token', response)

    def test_acquire_ignores_offsite_next(self):
        self.client.force_login(self.superuser)
        response = self.acquire(next='https://evil.example/')

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.example', response['Location'])

    def test_release_ignores_offsite_next(self):
        self.client.force_login(self.superuser)
        self.acquire()
        response = self.release(next='//evil.example/')

        self.assertEqual(response.status_code, 302)
        self.assertNotIn('evil.example', response['Location'])

    def test_acquire_honours_local_next(self):
        self.client.force_login(self.superuser)
        response = self.acquire(next='/en/admin/members/member/')

        self.assertEqual(response['Location'], '/en/admin/members/member/')

    def test_acquire_and_release_require_csrf_token(self):
        client = ApiClient(self.tenant, enforce_csrf_checks=True)
        client.force_login(self.superuser)

        self.assertEqual(self.acquire(client=client).status_code, 403)
        self.assertEqual(client.session.get('_auth_user_id'), str(self.superuser.pk))

        self.client.force_login(self.superuser)
        self.acquire()
        client.cookies = self.client.cookies
        response = client.post(self.release_url, {}, format='multipart')
        self.assertEqual(response.status_code, 403)

    def test_session_is_not_valid_on_other_tenant(self):
        self.staff.set_password('staff-password-tenant-1')
        self.staff.save()
        self.client.force_login(self.superuser)
        self.acquire()

        other_tenant = Client.objects.get(schema_name='test2')
        self.addCleanup(connection.set_tenant, self.tenant)
        with LocalTenant(other_tenant):
            BlueBottleUserFactory.create(
                pk=self.staff.pk, is_staff=True, is_superuser=False,
                password='staff-password-tenant-2'
            )

        index = self.client.get(reverse('admin:index'), HTTP_HOST=other_tenant.domain_url)
        self.assertEqual(index.status_code, 302)
        self.assertIn('login', index['Location'])

    def test_acquire_and_release_are_audited(self):
        self.client.force_login(self.superuser)

        with mock.patch.object(signals.logger, 'info') as info:
            self.acquire()
            self.release()

        entries = LogEntry.objects.filter(
            user=self.superuser, object_id=str(self.staff.pk)
        ).order_by('pk')
        self.assertEqual(
            [entry.change_message for entry in entries],
            ['Started impersonating', 'Stopped impersonating'],
        )
        self.assertEqual(
            [call.args[1:4] for call in info.call_args_list],
            [
                ('Started impersonating', self.superuser.pk, self.staff.pk),
                ('Stopped impersonating', self.superuser.pk, self.staff.pk),
            ],
        )


class MemberAdminImpersonateLinksTest(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        self.staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        self.member = BlueBottleUserFactory.create(is_staff=False)

    def change_page(self, obj, user=None):
        self.client.force_login(user or self.superuser)
        return self.client.get(reverse('admin:members_member_change', args=(obj.pk,)))

    def front_end_url(self, obj):
        return reverse('admin:members_member_login_as', args=(obj.pk,))

    def test_list_has_no_impersonation_columns(self):
        self.client.force_login(self.superuser)
        response = self.client.get(reverse('admin:members_member_changelist'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-hijack-user')
        self.assertNotContains(response, self.front_end_url(self.staff))
        self.assertNotContains(response, 'column-login_as_link')

    def test_staff_detail_has_back_office_and_front_end(self):
        response = self.change_page(self.staff)

        self.assertContains(response, 'data-hijack-user="{}"'.format(self.staff.pk))
        self.assertContains(response, 'Back-office')
        self.assertContains(response, self.front_end_url(self.staff))
        self.assertContains(response, 'Front-end')

    def test_member_detail_has_only_front_end(self):
        response = self.change_page(self.member)

        self.assertNotContains(response, 'data-hijack-user')
        self.assertContains(response, self.front_end_url(self.member))

    def test_inactive_member_detail_has_no_links(self):
        self.staff.is_active = False
        self.staff.save()
        response = self.change_page(self.staff)

        self.assertNotContains(response, 'data-hijack-user')
        self.assertNotContains(response, self.front_end_url(self.staff))

    def test_staff_viewer_gets_no_links(self):
        response = self.change_page(self.member, user=self.staff_member)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-hijack-user')
        self.assertNotContains(response, self.front_end_url(self.member))


class LoginAsAdminTest(BluebottleAdminTestCase):
    def setUp(self):
        super().setUp()
        self.member = BlueBottleUserFactory.create()
        self.url = reverse('admin:members_member_login_as', args=(self.member.pk,))

    def _confirm_login_as(self, user, member=None):
        target = member or self.member
        url = reverse('admin:members_member_login_as', args=(target.pk,))
        self.client.force_login(user)
        return self.client.post(
            url,
            {
                'confirm': 'Yes, I am sure',
                'action': 'login_as',
                ACTION_CHECKBOX_NAME: str(target.pk),
            },
            format='multipart',
        )

    def test_superuser_login_as_includes_impersonation_token(self):
        response = self._confirm_login_as(self.superuser)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('originalJwtToken', html)
        self.assertRegex(html, r'var token = ".+"')
        self.assertRegex(html, r'var originalToken = ".+"')

        payload = jwt.decode(
            self.member.get_jwt_token(impersonator=self.superuser),
            algorithms='HS256',
            options=dict(verify_signature=False)
        )
        original_payload = jwt.decode(
            self.superuser.get_jwt_token(),
            algorithms='HS256',
            options=dict(verify_signature=False)
        )

        self.assertTrue(payload['impersonated'])
        self.assertEqual(payload['impersonator'], self.superuser.pk)
        self.assertEqual(payload['username'], self.member.pk)
        self.assertEqual(original_payload['username'], self.superuser.pk)
        self.assertNotIn('impersonated', original_payload)

    def test_staff_cannot_login_as(self):
        self.client.force_login(self.staff_member)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_cannot_login_as_inactive_member(self):
        inactive = BlueBottleUserFactory.create(is_active=False)
        response = self._confirm_login_as(self.superuser, member=inactive)
        self.assertEqual(response.status_code, 403)


class JwtPayloadMiddlewareTest(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.superuser = BlueBottleUserFactory.create(is_staff=True, is_superuser=True)
        self.member = BlueBottleUserFactory.create()

    def get_request(self, token=None):
        headers = {'HTTP_AUTHORIZATION': 'JWT {}'.format(token)} if token else {}
        request = RequestFactory().get('/api/members/me', **headers)
        SlidingJwtTokenMiddleware(lambda request: None).process_request(request)
        return request

    def test_impersonation_token(self):
        request = self.get_request(self.member.get_jwt_token(impersonator=self.superuser))

        self.assertTrue(request.jwt_payload.get('impersonated'))
        self.assertEqual(request.jwt_payload.get('impersonator'), self.superuser.pk)

    def test_regular_token(self):
        request = self.get_request(self.member.get_jwt_token())

        self.assertEqual(request.jwt_payload.get('username'), self.member.pk)
        self.assertIsNone(request.jwt_payload.get('impersonated'))

    def test_invalid_token(self):
        request = self.get_request('not-a-token')

        self.assertIsNone(request.jwt_payload.get('impersonated'))

    def test_no_token(self):
        request = self.get_request()

        self.assertIsNone(request.jwt_payload.get('impersonated'))
