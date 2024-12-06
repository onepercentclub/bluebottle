# -*- coding: utf-8 -*-
from datetime import timedelta

import mock
from django.urls import reverse
from django.utils.timezone import now
from djmoney.money import Money
from rest_framework import status

import stripe

from bluebottle.funding.models import FundingPlatformSettings
from bluebottle.funding.tests.factories import (
    FundingFactory, BankAccountFactory, DonorFactory,
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
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        bank_account = BankAccountFactory.create(
            status="verified",
            connect_account=StripePayoutAccountFactory.create(
                account_id="test-account-id", status="verified"
            ),
        )
        self.funding = FundingFactory.create(
            owner=self.superuser,
            initiative=self.initiative,
            bank_account=bank_account
        )
        BudgetLineFactory.create(activity=self.funding)
        self.admin_url = reverse('admin:funding_funding_change', args=(self.funding.id, ))

    def test_funding_admin_review(self):
        self.client.force_login(self.superuser)
        self.funding.states.submit(save=True)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.funding.title)
        self.assertContains(response, 'approve')
        reviewed_url = reverse('admin:funding_funding_state_transition',
                               args=(self.funding.id, 'states', 'approve'))
        self.assertContains(response, reviewed_url)
        response = self.client.get(reviewed_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_funding_admin_future_deadline(self):
        self.client.force_login(self.superuser)
        self.funding.status = 'open'
        self.funding.save()
        DonorFactory.create(activity=self.funding)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_funding_admin_add_matching(self):
        self.funding.states.submit()
        self.funding.states.approve()
        self.funding.target = Money(100, 'EUR')
        self.funding.save()
        donation = DonorFactory.create(
            activity=self.funding,
            amount=Money(70, 'EUR')
        )
        donation.states.succeed(save=True)
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(self.funding.amount_raised, Money(70, 'EUR'))
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.assertEqual(self.funding.amount_raised, Money(70, 'EUR'))
        self.funding.amount_matching = Money(30, 'EUR')
        self.funding.save()

        self.client.force_login(self.superuser)
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.funding.title)

        self.assertContains(response, 'recalculate')
        recalculate_url = reverse('admin:funding_funding_state_transition',
                                  args=(self.funding.id, 'states', 'recalculate'))

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
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        account = StripePayoutAccountFactory.create(
            account_id="test-account-id", status="verified"
        )
        bank_account = ExternalAccountFactory.create(connect_account=account, status='verified')

        self.funding = FundingFactory.create(
            owner=self.superuser,
            initiative=self.initiative,
            bank_account=bank_account
        )
        self.admin_url = reverse('admin:funding_donor_changelist')

    def test_donation_total(self):
        for donation in DonorFactory.create_batch(
            2,
            activity=self.funding,
            amount=Money(100, 'NGN')
        ):
            PledgePaymentFactory.create(donation=donation)

        self.client.force_login(self.superuser)
        response = self.client.get(self.admin_url)
        self.assertTrue(
            u'Total amount:  <b>0.60 €</b>'.encode('utf-8') in response.content
        )

    def test_donation_admin_pledge_filter(self):
        for donation in DonorFactory.create_batch(2, activity=self.funding):
            PledgePaymentFactory.create(donation=donation)

        for donation in DonorFactory.create_batch(7, activity=self.funding):
            StripePaymentFactory.create(donation=donation)

        self.client.force_login(self.superuser)

        response = self.client.get(self.admin_url, {'status__exact': 'all'})
        self.assertContains(response, '9 Donations')

        response = self.client.get(self.admin_url, {'status__exact': 'all', 'pledge': 'paid'})
        self.assertContains(response, '7 Donations')

        response = self.client.get(self.admin_url, {'status__exact': 'all', 'pledge': 'pledged'})
        self.assertContains(response, '2 Donations')

    def test_donation_reward(self):
        donation = DonorFactory.create(activity=self.funding)

        url = reverse('admin:funding_donor_change', args=(donation.pk, ))
        first = RewardFactory.create(title='First', activity=self.funding)
        second = RewardFactory.create(title='Second', activity=self.funding)
        third = RewardFactory.create(title='Third')

        self.client.force_login(self.superuser)

        response = self.client.get(url)
        self.assertTrue(first.title in response.content.decode('utf-8'))
        self.assertTrue(second.title in response.content.decode('utf-8'))
        self.assertFalse(third.title in response.content.decode('utf-8'))


class PayoutAccountAdminTestCase(BluebottleAdminTestCase):

    def setUp(self):
        super(PayoutAccountAdminTestCase, self).setUp()
        self.payout_account = StripePayoutAccountFactory.create(
            account_id="test-account-id", status="verified"
        )
        self.bank_account = ExternalAccountFactory.create(connect_account=self.payout_account, status='verified')
        self.payout_account_url = reverse('admin:funding_payoutaccount_change', args=(self.payout_account.id,))
        self.bank_account_url = reverse('admin:funding_bankaccount_change', args=(self.bank_account.id,))
        self.client.force_login(self.superuser)

    def test_payout_account_admin(self):
        specs = stripe.ListObject()
        specs.data = []

        with mock.patch('stripe.CountrySpec.list', return_value=specs):
            response = self.client.get(self.payout_account_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_bank_account_admin(self):
        response = self.client.get(self.bank_account_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class FundingPlatformSettingsAdminTestCase(BluebottleAdminTestCase):
    extra_environ = {}
    csrf_checks = False
    setup_auth = True

    def setUp(self):
        super(FundingPlatformSettingsAdminTestCase, self).setUp()
        self.app.set_user(self.superuser)
        self.client.force_login(self.superuser)

    def test_anonymous_donations(self):
        funding_settings = FundingPlatformSettings.load()
        self.assertFalse(funding_settings.anonymous_donations)
        url = reverse('admin:funding_fundingplatformsettings_change')
        page = self.app.get(url)
        page = page.click('Funding settings')
        form = page.forms[0]
        form["anonymous_donations"] = True
        form.submit()

        funding_settings = FundingPlatformSettings.load()
        self.assertTrue(funding_settings.anonymous_donations)
