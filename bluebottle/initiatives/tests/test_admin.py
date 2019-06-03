# -*- coding: utf-8 -*-

from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.core import mail
from django.urls.base import reverse
from rest_framework import status

from bluebottle.files.tests.factories import ImageFactory
from bluebottle.initiatives.admin import InitiativeAdmin
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleAdminTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class TestInitiativeAdmin(BluebottleAdminTestCase):

    def setUp(self):
        super(TestInitiativeAdmin, self).setUp()
        self.site = AdminSite()
        self.initiative_admin = InitiativeAdmin(Initiative, self.site)
        self.initiative = InitiativeFactory.create(status='created')
        self.initiative.submit()
        self.initiative.save()

    def test_initiative_admin(self):
        image = ImageFactory.create()
        self.initiative.image = image
        self.initiative.save()
        self.client.force_login(self.superuser)
        admin_url = reverse('admin:initiatives_initiative_change',
                            args=(self.initiative.id,))
        response = self.client.get(admin_url)
        self.assertContains(response, image.id)

    def test_review_initiative_send_mail(self):
        self.client.force_login(self.superuser)
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'approve'))
        response = self.client.get(review_url)

        # Should show confirmation page
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Are you sure you want to change')

        # Confirm should change status
        response = self.client.post(review_url, {'confirm': True, 'send_messages': True})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, 'Should redirect back to initiative change')
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'approved')
        # Should send out one mail
        self.assertEqual(len(mail.outbox), 1)

    def test_review_initiative_send_no_mail(self):
        self.client.force_login(self.superuser)
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'approve'))
        response = self.client.get(review_url)

        # Should show confirmation page
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, 'Are you sure you want to change')

        # Confirm should change status
        response = self.client.post(review_url, {'confirm': True, 'send_messages': False})
        self.assertEqual(response.status_code, status.HTTP_302_FOUND, 'Should redirect back to initiative change')
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'approved')
        # No mail should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_review_initiative_illegal_transition(self):
        self.client.force_login(self.superuser)
        # reject the
        self.initiative.close()
        self.initiative.save()

        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'approve'))
        response = self.client.get(review_url)

        self.assertEqual(response.status_code, 302, 'Should redirect back to initiative change')

        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'closed')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Transition not allowed: approve')

    def test_review_initiative_unauthorized(self):
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'approve'))
        response = self.client.post(review_url, {'confirm': False})
        # Should redirect with message
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertTrue(response.url.startswith('/en/admin/login'))
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'submitted')

    def test_review_initiative_no_permission(self):
        self.client.force_login(BlueBottleUserFactory.create(is_staff=True))

        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'approve'))
        response = self.client.post(review_url, {'confirm': False})
        # Should redirect with message
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'submitted')

    def test_review_initiative_missing_field(self):
        self.client.force_login(self.superuser)
        self.initiative = InitiativeFactory.create(status='created', pitch='')
        self.assertEqual(self.initiative.status, 'created')
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'submit'))

        response = self.client.post(review_url, {'confirm': True})

        # Should redirect with error message
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'created')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages[0].message, 'Transition not allowed: submit')

    def test_review_initiative_missing_theme(self):
        self.client.force_login(self.superuser)
        self.initiative = InitiativeFactory.create(status='created', theme=None)
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'submit'))
        response = self.client.post(review_url, {'confirm': True})

        # Should redirect with error message
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'created')

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(messages[0].message, 'Transition not allowed: submit')
