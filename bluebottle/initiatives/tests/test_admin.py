# -*- coding: utf-8 -*-

from builtins import str
from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.core import mail
from django.urls.base import reverse
from rest_framework import status

from bluebottle.files.tests.factories import ImageFactory
from bluebottle.initiatives.admin import InitiativeAdmin
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.organizations import OrganizationContactFactory, OrganizationFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestInitiativeAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestInitiativeAdmin, self).setUp()
        self.site = AdminSite()
        self.initiative_admin = InitiativeAdmin(Initiative, self.site)
        self.initiative = InitiativeFactory.create()
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
        self.assertContains(response, 'Show on site')
        self.assertContains(response, 'Activities')
        self.assertContains(response, 'Messages')
        self.assertContains(response, 'Office location')
        self.assertContains(response, 'Impact location')

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
        self.client.force_login(self.superuser)
        user = BlueBottleUserFactory.create()
        admin_url = reverse('admin:initiatives_initiative_change', args=(self.initiative.id,))
        data = {
            'title': self.initiative.title,
            'slug': self.initiative.slug,
            'owner': self.initiative.owner_id,
            'image': '',
            'video_url': '',
            'pitch': self.initiative.pitch,
            'story': self.initiative.story,
            'theme': self.initiative.theme_id,
            'place': self.initiative.place_id,
            'has_organization': 2,
            'organization': '',
            'organization_contact': '',
            'reviewer': self.initiative.reviewer_id,
            'activity_manager': self.initiative.activity_manager_id,
            'promoter': '',
            '_continue': 'Save and continue editing',
            'activities-TOTAL_FORMS': '0',
            'activities-INITIAL_FORMS': '0',
            'notifications-message-content_type-object_id-TOTAL_FORMS': '0',
            'notifications-message-content_type-object_id-INITIAL_FORMS': '0',
            'wallposts-wallpost-content_type-object_id-TOTAL_FORMS': '0',
            'wallposts-wallpost-content_type-object_id-INITIAL_FORMS': '0'
        }
        response = self.client.post(admin_url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, admin_url)

        data['reviewer'] = user.id

        # Should show confirmation page
        response = self.client.post(admin_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Are you sure?')

        data['confirm'] = 'True'
        data['send_messages'] = 'on'
        response = self.client.post(admin_url, data)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, admin_url)
        self.initiative.refresh_from_db()
        self.assertEqual(self.initiative.reviewer, user)

        # Should send out one mail that contains admin url and contact email
        self.assertEqual(len(mail.outbox), 1)
        admin_url = '/admin/initiatives/initiative/{}/change'.format(self.initiative.id)
        self.assertTrue(admin_url in mail.outbox[0].body)
        self.assertTrue('contact@my-bluebottle-project.com' in mail.outbox[0].body)
