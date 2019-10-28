from django.urls import reverse
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, BankAccountFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleAdminTestCase


class FundingTestCase(BluebottleAdminTestCase):
    def setUp(self):
        super(FundingTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()
        bank_account = BankAccountFactory.create()
        self.funding = FundingFactory.create(
            owner=self.superuser,
            initiative=self.initiative,
            bank_account=bank_account
        )
        self.funding.review_transitions.submit()
        self.funding.save()
        self.admin_url = reverse('admin:funding_funding_change', args=(self.funding.id, ))

    def test_funding_admin(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.funding.title)
        self.assertContains(response, 'approve')
        reviewed_url = reverse('admin:funding_funding_transition',
                               args=(self.funding.id, 'review_transitions', 'approve'))
        self.assertContains(response, reviewed_url)

    def test_funding_admin_review(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.funding.title)
        self.assertContains(response, 'approve')
        reviewed_url = reverse('admin:funding_funding_transition',
                               args=(self.funding.id, 'review_transitions', 'approve'))

        self.assertContains(response, reviewed_url)
        response = self.client.get(reviewed_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
