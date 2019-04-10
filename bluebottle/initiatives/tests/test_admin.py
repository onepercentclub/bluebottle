# -*- coding: utf-8 -*-

from django.contrib.admin.sites import AdminSite
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

    def test_review_initiative(self):
        self.client.force_login(self.superuser)
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'accept'))
        response = self.client.get(review_url)

        # Should show confirmation page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Are you sure you want to change')

        # Confirm should change status
        response = self.client.post(review_url, {'confirm': True})
        self.assertEqual(response.status_code, 302, 'Should redirect back to initiative change')
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.review_status, 'accepted')

    def test_review_initiative_unauthorized(self):
        review_url = reverse('admin:initiatives_initiative_transition',
                             args=(self.initiative.id, 'accept'))
        response = self.client.post(review_url, {'confirm': False})
        # Should be denied
        self.assertEqual(response.status_code, 403)
        self.initiative = Initiative.objects.get(pk=self.initiative.id)
        self.assertEqual(self.initiative.review_status, 'submitted')
