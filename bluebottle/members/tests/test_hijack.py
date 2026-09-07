import jwt

from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.test import RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.plugins.otp_totp.models import TOTPDevice

from bluebottle.auth.middleware import HIJACK_OTP_DEVICE_SESSION_KEY, OTPMiddleware
from bluebottle.members.hijack import can_hijack
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleAdminTestCase, BluebottleTestCase


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

    def test_superuser_can_hijack_staff(self):
        self.assertTrue(can_hijack(hijacker=self.superuser, hijacked=self.staff))

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

    def test_hijacked_user_is_verified_without_matching_device(self):
        staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        staff.is_hijacked = True
        request = self.request_factory.get('/en/admin/')
        request.session = {DEVICE_ID_SESSION_KEY: 'totpdevice/1'}

        middleware = OTPMiddleware(get_response=lambda r: None)
        with override_settings(DISABLE_TWO_FACTOR=False):
            user = middleware._verify_user(request, staff)

        self.assertTrue(user.is_verified())
        self.assertIn(DEVICE_ID_SESSION_KEY, request.session)

    def test_unhijacked_user_without_device_is_not_verified(self):
        staff = BlueBottleUserFactory.create(is_staff=True, is_superuser=False)
        request = self.request_factory.get('/en/admin/')
        request.session = {}

        middleware = OTPMiddleware(get_response=lambda r: None)
        with override_settings(DISABLE_TWO_FACTOR=False):
            user = middleware._verify_user(request, staff)

        self.assertFalse(user.is_verified())


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
