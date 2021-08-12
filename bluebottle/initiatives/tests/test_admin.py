# -*- coding: utf-8 -*-

from builtins import str

from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.core import mail
from django.urls import reverse
from rest_framework import status
from rest_framework.status import HTTP_200_OK

from bluebottle.files.tests.factories import ImageFactory
from bluebottle.initiatives.admin import InitiativeAdmin, ThemeAdmin
from bluebottle.initiatives.models import Initiative, Theme, InitiativePlatformSettings
from bluebottle.initiatives.tests.factories import InitiativeFactory, InitiativePlatformSettingsFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationContactFactory, OrganizationFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.test.factory_models.geo import LocationFactory


class TestInitiativeAdmin(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(TestInitiativeAdmin, self).setUp()
        self.site = AdminSite()
        self.initiative_admin = InitiativeAdmin(Initiative, self.site)
        self.initiative = InitiativeFactory.create(
            title='The Dharma Initiative',
            reviewer=None
        )
        self.initiative.states.submit(save=True)

        self.approve_url = reverse(
            'admin:initiatives_initiative_state_transition',
            args=(self.initiative.id, 'states', 'approve')
        )

    def test_initiative_admin(self):
        image = ImageFactory.create()
        self.initiative.image = image
        self.initiative.save()
        self.client.force_login(self.superuser)
        admin_url = reverse('admin:initiatives_initiative_change',
                            args=(self.initiative.id,))
        response = self.client.get(admin_url)
        self.assertContains(response, image.id)
        self.assertContains(response, 'View on site')
        self.assertContains(response, 'Activities')
        self.assertContains(response, 'Messages')
        self.assertContains(response, 'Offices')
        self.assertContains(response, 'Impact location')

    def test_initiative_open(self):
        LocationFactory.create()
        self.initiative.is_open = True
        self.initiative.save()
        self.client.force_login(self.superuser)
        admin_url = reverse('admin:initiatives_initiative_change',
                            args=(self.initiative.id,))
        response = self.client.get(admin_url)
        self.assertContains(response, 'Is global')

    def test_initiative_closed(self):
        LocationFactory.create()
        self.initiative.is_open = False
        self.initiative.save()
        self.client.force_login(self.superuser)
        admin_url = reverse('admin:initiatives_initiative_change',
                            args=(self.initiative.id,))
        response = self.client.get(admin_url)
        self.assertNotContains(response, 'Is global')

    def test_initiative_admin_with_organization_contact(self):
        self.initiative.contact = OrganizationFactory.create()
        self.initiative.organization_contact = OrganizationContactFactory.create()
        self.initiative.has_organization = True
        self.initiative.save()
        self.assertIsNotNone(self.initiative.organization_contact)
        self.client.force_login(self.superuser)
        admin_url = reverse('admin:initiatives_initiative_change',
                            args=(self.initiative.id,))
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_review_initiative_send_mail(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.approve_url)

        # Should show confirmation page
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'You are about to')
        self.assertContains(response, 'Send messages')

        # Confirm should change status
        response = self.client.post(self.approve_url, {'confirm': True, 'send_messages': True})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, 'Should redirect back to initiative change')
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'approved')
        # Should send out one mail
        self.assertEqual(len(mail.outbox), 1)

    def test_review_initiative_send_no_mail(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.approve_url)

        # Should show confirmation page
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'You are about to')
        self.assertContains(response, 'Send messages')

        # Confirm should change status
        response = self.client.post(self.approve_url, {'confirm': True, 'send_messages': False})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, 'Should redirect back to initiative change')
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'approved')
        # No mail should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_review_initiative_request_changes(self):
        request_changes_url = reverse(
            'admin:initiatives_initiative_state_transition',
            args=(self.initiative.id, 'states', 'request_changes')
        )

        self.client.force_login(self.superuser)
        response = self.client.get(request_changes_url)

        # Should show confirmation page
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'You are about to')
        self.assertNotContains(response, 'Don\'t send any messages')

        # Confirm should change status
        response = self.client.post(self.approve_url, {'confirm': True, 'send_messages': True})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, 'Should redirect back to initiative change')
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'approved')

    def test_review_initiative_illegal_transition(self):
        self.client.force_login(self.superuser)
        # reject the
        self.initiative.states.reject(save=True)

        response = self.client.get(self.approve_url)
        self.assertEqual(response.status_code, 302, 'Should redirect back to initiative change')

        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'rejected')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Transition not possible: Approve')

    def test_review_initiative_unauthorized(self):
        response = self.client.post(self.approve_url, {'confirm': False})
        # Should redirect with message
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(response.url.startswith('/en/admin/login'))
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'submitted')

    def test_review_initiative_no_permission(self):
        self.client.force_login(BlueBottleUserFactory.create(is_staff=True))

        response = self.client.post(self.approve_url, {'confirm': False})
        # Should redirect with message
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'submitted')

    def test_hide_delete_transition(self):
        initiative = InitiativeFactory.create()
        self.client.force_login(self.superuser)
        admin_url = reverse('admin:initiatives_initiative_change', args=(initiative.pk,))

        response = self.client.get(admin_url)
        self.assertFalse(
            '/en/admin/initiatives/initiative/{}/transition/states/delete'.format(
                initiative.pk
            ) in response.content.decode('utf-8')
        )

    def test_add_reviewer(self):
        self.app.set_user(self.staff_member)
        reviewer = BlueBottleUserFactory.create()
        admin_url = reverse('admin:initiatives_initiative_change', args=(self.initiative.id,))
        page = self.app.get(admin_url)
        form = page.forms['initiative_form']
        form.set('reviewer', reviewer.id)
        page = form.submit()
        self.assertTrue('<h3>Send email</h3>' in page.text)
        form = page.forms[0]
        form.submit()

        # Should send out one mail that contains admin url and contact email
        self.assertEqual(len(mail.outbox), 1)
        admin_url = '/admin/initiatives/initiative/{}/change'.format(self.initiative.id)
        self.assertTrue(admin_url in mail.outbox[0].body)
        self.assertTrue('contact@my-bluebottle-project.com' in mail.outbox[0].body)
        self.initiative.refresh_from_db()
        self.assertEqual(self.initiative.reviewer, reviewer)

    def test_add_reviewer_cancel(self):
        self.app.set_user(self.staff_member)
        reviewer = BlueBottleUserFactory.create()
        admin_url = reverse('admin:initiatives_initiative_change', args=(self.initiative.id,))
        page = self.app.get(admin_url)
        form = page.forms['initiative_form']
        form.set('reviewer', reviewer.id)
        page = form.submit()
        self.assertTrue('<h3>Send email</h3>' in page.text)
        page.click('No, take me back')

        self.assertEqual(len(mail.outbox), 0)
        self.initiative.refresh_from_db()
        self.assertNotEqual(self.initiative.reviewer, reviewer)

    def test_add_reviewer_without_titlte(self):
        initiative = InitiativeFactory.create(title='')
        self.app.set_user(self.staff_member)
        reviewer = BlueBottleUserFactory.create()
        admin_url = reverse('admin:initiatives_initiative_change', args=(initiative.id,))
        page = self.app.get(admin_url)
        form = page.forms['initiative_form']
        form.set('reviewer', reviewer.id)
        page = form.submit()
        self.assertTrue('<h3>Send email</h3>' in page.text)
        page.click('No, take me back')

        self.assertEqual(len(mail.outbox), 0)
        self.initiative.refresh_from_db()
        self.assertNotEqual(initiative.reviewer, reviewer)

    def test_admin_open_initiative_disabled(self):
        initiative = InitiativeFactory.create()
        url = reverse('admin:initiatives_initiative_change', args=(initiative.id,))

        self.app.set_user(self.staff_member)
        page = self.app.get(url)
        self.assertFalse('is_open' in page.forms[0].fields)

    def test_admin_open_initiative_enabled(self):
        InitiativePlatformSettingsFactory.create(
            enable_open_initiatives=True
        )
        initiative = InitiativeFactory.create()
        url = reverse('admin:initiatives_initiative_change', args=(initiative.id,))
        self.app.set_user(self.staff_member)
        page = self.app.get(url)
        self.assertTrue('is_open' in page.forms[0].fields)

    def test_global_initiative_set(self):
        initiative_settings = InitiativePlatformSettings.load()
        initiative_settings.enable_open_initiatives = True
        initiative_settings.save()
        locations = LocationFactory.create_batch(5)
        initiative = InitiativeFactory.create(
            is_open=True,
            location=locations[0]
        )
        url = reverse('admin:initiatives_initiative_change', args=(initiative.id,))
        self.app.set_user(self.staff_member)
        page = self.app.get(url)
        form = page.forms[0]
        self.assertTrue('is_open' in form.fields)
        self.assertTrue('is_global' in form.fields)
        self.assertTrue('location' in form.fields)
        form['is_global'] = True
        page = form.submit()
        self.assertTrue('<h3>Remove location</h3>' in page.text)
        form = page.forms[0]
        page = form.submit().follow()
        url = reverse('admin:initiatives_initiative_change', args=(initiative.id,))
        self.app.set_user(self.staff_member)
        page = self.app.get(url)
        form = page.forms[0]
        self.assertTrue('is_global' in form.fields)
        self.assertFalse('location' in form.fields)

    def test_paginated_activities(self):
        self.app.set_user(self.staff_member)
        admin_url = reverse('admin:initiatives_initiative_change', args=(self.initiative.id,))
        page = self.app.get(admin_url)
        self.assertTrue('<span class="btn-page page-selected">1</span>' in page.text)


class TestThemeAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestThemeAdmin, self).setUp()
        self.site = AdminSite()
        self.skill_admin = ThemeAdmin(Theme, self.site)
        self.client.force_login(self.superuser)
        InitiativeFactory.create()

    def test_theme_admin_list(self):
        url = reverse('admin:initiatives_theme_changelist')
        response = self.client.get(url)
        self.assertTrue(response, HTTP_200_OK)

    def test_theme_admin_staf(self):
        url = reverse('admin:initiatives_theme_changelist')
        response = self.app.get(url, user=self.staff_member)
        self.assertEqual(response.status, '200 OK')


class TestInitiativePlatformSettingsAdmin(BluebottleAdminTestCase):

    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def test_admin_open_initiative_disabled(self):
        # Check multiple input shows labels
        url = reverse('admin:initiatives_initiativeplatformsettings_changelist')
        self.app.set_user(self.superuser)
        page = self.app.get(url)
        input_html = page.html.find('div', {'class': 'field-activity_types'}).text
        self.assertTrue('Deed' in input_html)
        self.assertTrue('Funding' in input_html)
