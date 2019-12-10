from datetime import timedelta

from django.urls import reverse
from django.utils.timezone import now
from djmoney.money import Money
from rest_framework import status

from bluebottle.funding.tests.factories import (
    FundingFactory, BankAccountFactory, DonationFactory,
    BudgetLineFactory, RewardFactory
)
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentFactory, StripePayoutAccountFactory, \
    ExternalAccountFactory
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
        BudgetLineFactory.create(activity=self.funding)
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

    def test_funding_admin_refund(self):
        self.funding.review_transitions.approve()
        self.funding.target = Money(100, 'EUR')
        donation = DonationFactory.create(
            activity=self.funding,
            amount=Money(70, 'EUR'))
        payment = PledgePaymentFactory.create(donation=donation)
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.funding.transitions.partial()
        self.funding.save()

        self.client.force_login(self.superuser)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.funding.title)
        self.assertContains(response, 'refund')
        refund_url = reverse('admin:funding_funding_transition',
                             args=(self.funding.id, 'transitions', 'refund'))

        self.assertContains(response, refund_url)
        self.client.post(refund_url, {'confirm': True})
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'refunded')
        donation.refresh_from_db()
        self.assertEqual(donation.status, 'refunded')
        payment.refresh_from_db()
        self.assertEqual(payment.status, 'refunded')

    def test_funding_admin_add_matching(self):
        self.funding.review_transitions.approve()
        self.funding.target = Money(100, 'EUR')
        donation = DonationFactory.create(
            activity=self.funding,
            amount=Money(70, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(self.funding.amount_raised, Money(70, 'EUR'))
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.funding.transitions.partial()
        self.funding.save()
        self.assertEqual(self.funding.amount_raised, Money(70, 'EUR'))

        self.funding.amount_matching = Money(30, 'EUR')
        self.funding.save()

        self.client.force_login(self.superuser)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.funding.title)
        self.assertContains(response, 'refund')
        recalculate_url = reverse('admin:funding_funding_transition',
                                  args=(self.funding.id, 'transitions', 'recalculate'))

        self.assertContains(response, recalculate_url)
        self.client.post(recalculate_url, {'confirm': True})
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'succeeded')
        self.funding.save()
        self.assertEqual(self.funding.amount_raised, Money(100, 'EUR'))


class DonationAdminTestCase(BluebottleAdminTestCase):

    def setUp(self):
        super(DonationAdminTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.initiative.save()
        account = StripePayoutAccountFactory.create()
        bank_account = ExternalAccountFactory.create(connect_account=account)

        self.funding = FundingFactory.create(
            owner=self.superuser,
            initiative=self.initiative,
            bank_account=bank_account
        )
        self.admin_url = reverse('admin:funding_donation_changelist')

    def test_donation_admin_pledge_filter(self):
        for donation in DonationFactory.create_batch(2, activity=self.funding):
            PledgePaymentFactory.create(donation=donation)

        for donation in DonationFactory.create_batch(7, activity=self.funding):
            StripePaymentFactory.create(donation=donation)

        self.client.force_login(self.superuser)

        response = self.client.get(self.admin_url, {'status__exact': 'all'})
        self.assertContains(response, '9 Donations')

        response = self.client.get(self.admin_url, {'status__exact': 'all', 'pledge': 'paid'})
        self.assertContains(response, '7 Donations')

        response = self.client.get(self.admin_url, {'status__exact': 'all', 'pledge': 'pledged'})
        self.assertContains(response, '2 Donations')

    def test_donation_reward(self):
        donation = DonationFactory.create(activity=self.funding)

        url = reverse('admin:funding_donation_change', args=(donation.pk, ))
        first = RewardFactory.create(title='First', activity=self.funding)
        second = RewardFactory.create(title='Second', activity=self.funding)
        third = RewardFactory.create(title='Third')

        self.client.force_login(self.superuser)

        response = self.client.get(url)
        self.assertTrue(first.title in response.content)
        self.assertTrue(second.title in response.content)
        self.assertFalse(third.title in response.content)
