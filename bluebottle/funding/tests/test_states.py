from datetime import timedelta

from django.core import mail
from django.utils.timezone import now
from djmoney.money import Money

from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, BankAccountFactory, \
    PlainPayoutAccountFactory, DonationFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = PlainPayoutAccountFactory.create()
        self.bank_account = BankAccountFactory.create(connect_account=payout_account)
        self.funding.bank_account = self.bank_account
        self.funding.save()

    def test_submit(self):
        self.assertEqual(self.funding.status, FundingStateMachine.submitted.value)

    def test_submit_incomplete(self):
        funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        funding.bank_account = self.bank_account
        funding.save()
        with self.assertRaisesMessage(TransitionNotPossible, 'Conditions not met for transition'):
            funding.states.submit()

    def test_submit_invalid(self):
        funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        funding.bank_account = self.bank_account
        funding.save()
        with self.assertRaisesMessage(TransitionNotPossible, 'Conditions not met for transition'):
            funding.states.submit()

    def test_approve(self):
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.open.value)

    def test_approve_organizer_succeed(self):
        self.funding.states.approve(save=True)
        organizer = self.funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_approve_set_start_dat(self):
        self.funding.states.approve(save=True)
        organizer = self.funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.succeeded.value)

    def test_approve_set_deadline(self):
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR'),
            deadline=None,
            duration=7
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = PlainPayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account)
        self.funding.bank_account = bank_account
        self.funding.save()
        self.funding.states.approve(save=True)
        next_week = now() + timedelta(days=7)
        self.assertEqual(self.funding.deadline.date(), next_week.date())

    def test_approve_should_close(self):

        self.funding.deadline = now() - timedelta(days=5)
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, 'closed')

    def _prepare_extend(self):
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.open.value)
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        # Changing the deadline to the past should trigger a transition
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.partially_funded.value)

    def test_extend(self):
        self._prepare_extend()
        # Changing the deadline to the future should open the campaign again
        self.funding.deadline = now() + timedelta(days=7)
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'open')

    def test_extend_delete_payouts(self):
        self._prepare_extend()
        self.assertEqual(self.funding.payouts.count(), 1)
        # Changing the deadline to the future should open the campaign again
        self.funding.deadline = now() + timedelta(days=7)
        self.funding.save()
        self.assertEqual(self.funding.payouts.count(), 0)

    def test_reject(self):
        self.funding.states.reject(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.rejected.value)
        organizer = self.funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.failed.value)

    def test_delete(self):
        self.funding.states.delete(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.deleted.value)
        organizer = self.funding.contributions.get()
        self.assertEqual(organizer.status, OrganizerStateMachine.failed.value)

    def _prepare_succeeded(self):
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, 'open')
        donation = DonationFactory.create(activity=self.funding, amount=Money(1000, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.funding.deadline = now() - timedelta(days=1)

    def test_succeed(self):
        self._prepare_succeeded()
        self.funding.states.succeed(save=True)
        self.assertEqual(self.funding.status, 'succeeded')

    def test_succeed_owner_message(self):
        self._prepare_succeeded()
        mail.outbox = []
        self.funding.states.succeed(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'You successfully completed your crowdfunding campaign! \U0001f389'
        )

    def test_succeed_generate_payouts(self):
        self._prepare_succeeded()
        self.funding.states.succeed(save=True)
        self.assertEqual(self.funding.status, 'succeeded')
        self.assertEqual(self.funding.payouts.count(), 1)
        self.assertEqual(self.funding.payouts.first().total_amount, Money(1000, 'EUR'))

    def test_close(self):
        mail.outbox = []
        self.funding.states.approve(save=True)
        self.funding.states.close(save=True)
        self.assertEqual(self.funding.status, 'closed')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'Your crowdfunding campaign has been closed'
        )

    def test_close_with_donations(self):
        mail.outbox = []
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        with self.assertRaisesMessage(
                TransitionNotPossible,
                'Conditions not met for transition'):
            self.funding.states.close(save=True)


class DonationStateMachineTests(BluebottleTestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = PlainPayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account)
        self.funding.bank_account = bank_account
        self.funding.save()

    def test_transitions_succeed(self):
        pass

    def test_transitions_fail(self):
        pass

    def test_transitions_refund(self):
        pass

    def test_transitions_refund_activity(self):
        pass

    def test_change_amount_and_deadline(self):
        self.assertEqual(self.funding.status, FundingStateMachine.submitted.value)
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, FundingStateMachine.open.value)
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        # Changing the deadline and target should transition the campaign to succeeded
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.target = Money(500, 'EUR')
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, FundingStateMachine.succeeded.value)

    def test_funding_amount_get_updated_after_donation(self):
        self.assertEqual(1, 0)
