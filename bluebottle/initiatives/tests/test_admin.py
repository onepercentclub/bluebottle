# -*- coding: utf-8 -*-

from django.contrib.admin.sites import AdminSite
from django.contrib.messages import get_messages
from django.core import mail
from django.urls.base import reverse

from bluebottle.initiatives.admin import InitiativeAdmin
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class TestInitiativeAdmin(BluebottleAdminTestCase):
    def setUp(self):
        super(TestInitiativeAdmin, self).setUp()
        self.site = AdminSite()
        self.initiative_admin = InitiativeAdmin(Initiative, self.site)
        self.initiative = InitiativeFactory.create()
        self.initiative.submit()
        self.initiative.save()

    def test_review_initiative_send_mail(self):
        self.client.force_login(self.superuser)
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'approve'))
        response = self.client.get(review_url)

        # Should show confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Are you sure you want to change')

        # Confirm should change status
        response = self.client.post(review_url, {'confirm': True, 'send_messages': True})
        self.assertEqual(response.status_code, 302, 'Should redirect back to initiative change')
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
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Are you sure you want to change')

        # Confirm should change status
        response = self.client.post(review_url, {'confirm': True, 'send_messages': False})
        self.assertEqual(response.status_code, 302, 'Should redirect back to initiative change')
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'approved')
        # No mail should be sent
        self.assertEqual(len(mail.outbox), 0)

    def test_review_initiative_illegal_transition(self):
        self.client.force_login(self.superuser)
        # reject the
        self.initiative.reject()
        self.initiative.save()

        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'approve'))
        response = self.client.get(review_url)

        # Should show confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Are you sure you want to change')

        # Confirm should change status
        response = self.client.post(review_url, {'confirm': True})
        self.assertEqual(response.status_code, 302, 'Should redirect back to initiative change')
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'rejected')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Transition not allowed: approve')

    def test_review_initiative_unauthorized(self):
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'approve'))
        response = self.client.post(review_url, {'confirm': False})
        # Should redirect with message
        self.assertEqual(response.status_code, 302)
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.status, 'submitted')
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), 'Missing permission: initiative.change_initiative')
