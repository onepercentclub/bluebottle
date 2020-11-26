from datetime import timedelta

from django.utils.timezone import now
from djmoney.money import Money

from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, BankAccountFactory, \
    PlainPayoutAccountFactory, DonorFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingTriggerTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = PlainPayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account, status='verified')
        self.funding.bank_account = bank_account
        self.funding.states.submit(save=True)

    def test_trigger_matching(self):
        self.assertEqual(self.funding.status, FundingStateMachine.submitted.value)
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.open.value)
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        # Changing the deadline to the past should trigger a transition
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.partially_funded.value)
        # Add amount matched funding to complete the project should transition it to succeeded
        self.funding.amount_matching = Money(500, 'EUR')
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.succeeded.value)

    def test_trigger_lower_target(self):
        self.assertEqual(self.funding.status, FundingStateMachine.submitted.value)
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.open.value)
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        # Changing the deadline to the past should trigger a transition
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.partially_funded.value)
        # Lower target of the project should transition it to succeeded
        self.funding.target = Money(500, 'EUR')
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.succeeded.value)


class DonorTriggerTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = PlainPayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account, status='verified')
        self.funding.bank_account = bank_account
        self.funding.states.submit(save=True)
        self.donor = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        self.payment = PledgePaymentFactory.create(donation=self.donor)

    def test_change_donor_amount(self):
        self.assertEqual(self.donor.amount, Money(500, 'EUR'))
        self.assertEqual(self.donor.payout_amount, Money(500, 'EUR'))
        contribution = self.donor.contributions.get()
        self.assertEqual(contribution.amount, Money(500, 'EUR'))
        self.assertEqual(self.funding.amount_donated, Money(500, 'EUR'))

        self.donor.amount = Money(200, 'EUR')
        self.donor.payout_amount = Money(200, 'EUR')
        self.donor.save()

        self.funding.refresh_from_db()
        self.assertEqual(self.donor.amount, Money(200, 'EUR'))
        self.assertEqual(self.donor.payout_amount, Money(200, 'EUR'))
        contribution = self.donor.contributions.get()
        self.assertEqual(contribution.amount, Money(200, 'EUR'))
        self.assertEqual(self.funding.amount_donated, Money(200, 'EUR'))
