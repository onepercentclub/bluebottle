from builtins import str
from datetime import timedelta

import mock
from django.utils.timezone import now
from moneyed import Money

from bluebottle.activities.tasks import data_retention_contribution_task

from bluebottle.funding.models import Payout
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, RewardFactory, DonorFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentFactory, StripePayoutAccountFactory, ExternalAccountFactory
)

from bluebottle.members.models import MemberPlatformSettings

from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingTestCase(BluebottleTestCase):

    def test_absolute_url(self):
        funding = FundingFactory()
        expected = 'http://testserver/en/initiatives/activities/details' \
                   '/funding/{}/{}'.format(funding.id, funding.slug)
        self.assertEqual(funding.get_absolute_url(), expected)

    def test_amount_donated(self):
        funding = FundingFactory.create(target=Money(100, 'EUR'))
        DonorFactory.create_batch(3, activity=funding, amount=Money(30, 'EUR'), status="succeeded")

        funding.refresh_from_db()

        self.assertEqual(funding.amount_donated, Money(90, 'EUR'))
        self.assertEqual(funding.amount_pledged, Money(0, 'EUR'))
        self.assertEqual(funding.genuine_amount_donated, Money(90, 'EUR'))

    def test_amount_donated_pledge(self):
        funding = FundingFactory.create(target=Money(100, 'EUR'))

        pledge = DonorFactory.create(activity=funding, amount=Money(30, 'EUR'))
        PledgePaymentFactory.create(donation=pledge)

        DonorFactory.create_batch(3, activity=funding, amount=Money(30, 'EUR'), status="succeeded")

        funding.refresh_from_db()

        self.assertEqual(funding.amount_donated, Money(120, 'EUR'))
        self.assertEqual(funding.amount_pledged, Money(30, 'EUR'))
        self.assertEqual(funding.genuine_amount_donated, Money(90, 'EUR'))

    def test_amount_donated_anonimised(self):
        member_settings = MemberPlatformSettings.load()
        member_settings.retention_delete = 10
        member_settings.retention_anonymize = 6
        member_settings.save()

        funding = FundingFactory.create(target=Money(100, 'EUR'))
        donors = DonorFactory.create_batch(3, activity=funding, amount=Money(30, 'EUR'))
        for donor in donors:
            donor.states.succeed(save=True)

        old_donation = DonorFactory.create(
            activity=funding, amount=Money(30, 'EUR'), created=now() - timedelta(days=330)
        )
        old_donation.states.succeed(save=True)

        funding.refresh_from_db()
        self.assertEqual(len(funding.donations), 4)
        self.assertEqual(funding.amount_donated, Money(120, 'EUR'))
        self.assertEqual(funding.amount_pledged, Money(0, 'EUR'))
        self.assertEqual(funding.genuine_amount_donated, Money(120, 'EUR'))

        data_retention_contribution_task()
        funding.update_amounts()

        funding.refresh_from_db()
        self.assertEqual(len(funding.donations), 3)
        self.assertEqual(funding.amount_donated, Money(120, 'EUR'))
        self.assertEqual(funding.amount_pledged, Money(0, 'EUR'))
        self.assertEqual(funding.genuine_amount_donated, Money(120, 'EUR'))

    def test_budget_currency_change(self):
        funding = FundingFactory.create(target=Money(100, 'EUR'))

        BudgetLineFactory.create_batch(5, activity=funding, amount=Money(20, 'EUR'))

        funding.target = Money(50, 'USD')
        funding.save()

        for line in funding.budget_lines.all():
            self.assertEqual(str(line.amount.currency), 'USD')

    def test_budget_line_required(self):
        funding = FundingFactory.create(target=Money(100, 'EUR'))
        errors = list(funding.errors)

        self.assertEqual(len(errors), 2)
        self.assertEqual(errors[1].message, 'Please specify a budget')

        BudgetLineFactory.create_batch(5, activity=funding, amount=Money(20, 'EUR'))

        errors = list(funding.errors)
        self.assertEqual(len(errors), 1)

    def test_reward_currency_change(self):
        funding = FundingFactory.create(target=Money(100, 'EUR'))

        RewardFactory.create_batch(5, activity=funding, amount=Money(20, 'EUR'))

        funding.target = Money(50, 'USD')
        funding.save()

        for reward in funding.rewards.all():
            self.assertEqual(str(reward.amount.currency), 'USD')

    def test_deadline_in_past(self):
        funding = FundingFactory.create(
            target=Money(100, 'EUR'), deadline=now() - timedelta(days=10), status='in_review'
        )

        errors = list(funding.errors)
        self.assertEqual(len(errors), 3)

        self.assertEqual(errors[1].message, 'Make sure the deadline is in the future.')

    def test_deadline_in_past_with_duration(self):
        funding = FundingFactory.create(
            target=Money(100, 'EUR'),
            deadline=now() - timedelta(days=10),
            duration=10,
            status='in_review'
        )

        errors = list(funding.errors)
        self.assertEqual(len(errors), 2)

    def test_deadline_in_past_succeeded(self):
        funding = FundingFactory.create(
            target=Money(100, 'EUR'), deadline=now() - timedelta(days=10), status='succeeded'
        )

        errors = [error.message for error in list(funding.errors)]
        self.assertEqual(
            errors,
            [
                u'Make sure your payout account is verified',
                u'Please specify a budget'
            ]
        )


class PayoutTestCase(BluebottleTestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            duration=30,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create(reviewed=True, status='verified')
        self.bank_account = ExternalAccountFactory.create(connect_account=payout_account, status='verified')
        self.funding.bank_account = self.bank_account
        self.funding.states.submit()
        self.funding.states.approve(save=True)

        for donation in DonorFactory.create_batch(
                3,
                amount=Money(150, 'EUR'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        for donation in DonorFactory.create_batch(
                2,
                amount=Money(200, 'USD'),
                payout_amount=(150, 'EUR'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        for donation in DonorFactory.create_batch(
                5,
                amount=Money(100, 'USD'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        donation = DonorFactory.create(
            amount=Money(750, 'EUR'),
            activity=self.funding,
            status='succeeded')
        PledgePaymentFactory.create(donation=donation)

        self.donation = donation

        for donation in DonorFactory.create_batch(
                5,
                amount=Money(150, 'EUR'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        for donation in DonorFactory.create_batch(
                5,
                amount=Money(100, 'USD'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

    def test_auto_generate_payouts(self):
        self.funding.states.succeed()
        self.funding.save()
        self.assertEqual(self.funding.payouts.count(), 3)

    def test_generate_payouts(self):
        Payout.generate(self.funding)
        self.assertEqual(self.funding.payouts.count(), 3)
        payout_amounts = [p.total_amount for p in self.funding.payouts.all()]
        self.assertTrue(Money(1000, 'USD') in payout_amounts)
        self.assertTrue(Money(1500, 'EUR') in payout_amounts)
        self.assertTrue(Money(750, 'EUR') in payout_amounts)

        # More donations
        for donation in DonorFactory.create_batch(5,
                                                  amount=Money(150, 'EUR'),
                                                  activity=self.funding,
                                                  status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        # Recalculate should generate new payouts. One should be higher now.
        Payout.generate(self.funding)
        self.assertEqual(self.funding.payouts.count(), 3)
        payout_amounts = [p.total_amount for p in self.funding.payouts.all()]
        self.assertTrue(Money(1000, 'USD') in payout_amounts)
        self.assertTrue(Money(2250, 'EUR') in payout_amounts)
        self.assertTrue(Money(750, 'EUR') in payout_amounts)

        with mock.patch('bluebottle.payouts_dorado.adapters.DoradoPayoutAdapter.trigger_payout'):
            for payout in self.funding.payouts.all():
                payout.states.approve()
                payout.save()

        # More donations after approved payouts
        for donation in DonorFactory.create_batch(8,
                                                  amount=Money(250, 'EUR'),
                                                  activity=self.funding,
                                                  status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        # Recalculate should generate an additional payout
        Payout.generate(self.funding)
        self.assertEqual(self.funding.payouts.count(), 4)
        payout_amounts = [p.total_amount for p in self.funding.payouts.all()]
        self.assertTrue(Money(1000, 'USD') in payout_amounts)
        self.assertTrue(Money(2000, 'EUR') in payout_amounts)
        self.assertTrue(Money(2250, 'EUR') in payout_amounts)
        self.assertTrue(Money(750, 'EUR') in payout_amounts)
