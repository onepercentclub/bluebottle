from datetime import timedelta

import mock
from django.utils.timezone import now
from moneyed import Money

from bluebottle.funding.models import Payout
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, RewardFactory, DonationFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentFactory, StripePayoutAccountFactory, \
    ExternalAccountFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingTestCase(BluebottleTestCase):

    def test_absolute_url(self):
        funding = FundingFactory()
        expected = 'http://testserver/en/initiatives/activities/details' \
                   '/funding/{}/{}'.format(funding.id, funding.slug)
        self.assertEqual(funding.get_absolute_url(), expected)

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
        self.assertEqual(errors[1].message, ['Please specify a budget'])

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


class PayoutTestCase(BluebottleTestCase):

    def setUp(self):
        account = StripePayoutAccountFactory.create()
        bank_account = ExternalAccountFactory.create(connect_account=account)
        self.funding = FundingFactory(
            deadline=now() + timedelta(days=10),
            target=Money(4000, 'EUR'),
            bank_account=bank_account
        )
        self.funding.transitions.reviewed()
        self.funding.save()

        for donation in DonationFactory.create_batch(
                5,
                amount=Money(150, 'EUR'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        for donation in DonationFactory.create_batch(
                5,
                amount=Money(100, 'USD'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        donation = DonationFactory.create(
            amount=Money(750, 'EUR'),
            activity=self.funding,
            status='succeeded')
        PledgePaymentFactory.create(donation=donation)

        for donation in DonationFactory.create_batch(
                5,
                amount=Money(150, 'EUR'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        for donation in DonationFactory.create_batch(
                5,
                amount=Money(100, 'USD'),
                activity=self.funding,
                status='succeeded'):
            StripePaymentFactory.create(donation=donation)

    def test_auto_generate_payouts(self):
        self.funding.transitions.succeed()
        self.funding.save()
        self.assertEqual(self.funding.payouts.count(), 3)

    def test_generate_payouts(self):
        Payout.generate(self.funding)
        self.assertEqual(self.funding.payouts.count(), 3)

        self.assertEqual(self.funding.payouts.all()[0].total_amount, Money(1000, 'USD'))
        self.assertEqual(self.funding.payouts.all()[1].total_amount, Money(1500, 'EUR'))
        self.assertEqual(self.funding.payouts.all()[2].total_amount, Money(750, 'EUR'))

        # More donations
        for donation in DonationFactory.create_batch(5,
                                                     amount=Money(150, 'EUR'),
                                                     activity=self.funding,
                                                     status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        # Recalculate should generate new payouts. One should be higher now.
        Payout.generate(self.funding)
        self.assertEqual(self.funding.payouts.count(), 3)
        self.assertEqual(self.funding.payouts.all()[0].total_amount, Money(1000, 'USD'))
        self.assertEqual(self.funding.payouts.all()[1].total_amount, Money(2250, 'EUR'))
        self.assertEqual(self.funding.payouts.all()[2].total_amount, Money(750, 'EUR'))

        with mock.patch('bluebottle.payouts_dorado.adapters.DoradoPayoutAdapter.trigger_payout'):
            for payout in self.funding.payouts.all():
                payout.transitions.approve()
                payout.save()

        # More donations after approved payouts
        for donation in DonationFactory.create_batch(8,
                                                     amount=Money(250, 'EUR'),
                                                     activity=self.funding,
                                                     status='succeeded'):
            StripePaymentFactory.create(donation=donation)

        # Recalculate should generate an additional payout
        Payout.generate(self.funding)
        self.assertEqual(self.funding.payouts.count(), 4)

        self.assertEqual(self.funding.payouts.all()[0].total_amount, Money(2000, 'EUR'))
        self.assertEqual(self.funding.payouts.all()[1].total_amount, Money(1000, 'USD'))
        self.assertEqual(self.funding.payouts.all()[2].total_amount, Money(2250, 'EUR'))
        self.assertEqual(self.funding.payouts.all()[3].total_amount, Money(750, 'EUR'))
