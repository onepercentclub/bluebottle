from datetime import timedelta

from django.core import mail
from django.utils.timezone import now
from djmoney.money import Money
from mock import patch

from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, BankAccountFactory, \
    PlainPayoutAccountFactory, DonationFactory
from bluebottle.funding_flutterwave.tests.factories import FlutterwavePaymentFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentFactory, StripePayoutAccountFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.wallposts.models import Wallpost


class StripeSourcePaymentStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create()
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
        self.funding.states.approve(save=True)

    def test_initiate(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        self.assertEqual(donation.status, 'new')

    def test_succeed(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(donation.status, 'succeeded')

    def test_succeed_update_amounts(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(self.funding.amount_raised, Money(500, 'EUR'))

    def test_succeed_generate_wallpost(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        wallpost = Wallpost.objects.last()
        self.assertEqual(wallpost.donation, donation)

    def test_succeed_mail_supporter(self):
        mail.outbox = []
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(mail.outbox[0].subject, u'You have a new donation!\U0001f4b0')

    def test_succeed_mail_activity_manager(self):
        mail.outbox = []
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(mail.outbox[1].subject, u'Thanks for your donation!')

    def test_succeed_follow(self):
        mail.outbox = []
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertTrue(self.funding.followers.filter(user=donation.user).exists())

    def test_fail(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.fail(save=True)
        self.assertEqual(donation.status, 'failed')

    def test_fail_update_amounts(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        donation = DonationFactory.create(activity=self.funding, amount=Money(250, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(self.funding.amount_raised, Money(750, 'EUR'))
        donation.states.fail(save=True)
        self.assertEqual(self.funding.amount_raised, Money(500, 'EUR'))

    def test_fail_remove_wallpost(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(Wallpost.objects.count(), 1)
        donation.states.fail(save=True)
        self.assertEqual(Wallpost.objects.count(), 0)

    def test_refund(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, 'succeeded')
        donation.states.refund(save=True)
        self.assertEqual(donation.status, 'refunded')

    def test_refund_payment_request_refund(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = FlutterwavePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        with patch('bluebottle.funding_flutterwave.models.FlutterwavePayment.refund') as refund:
            donation.states.activity_refund(save=True)
            refund.assert_called_once()
        self.assertEqual(payment.status, 'refund_requested')

    def test_refund_remove_wallpost(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(Wallpost.objects.count(), 1)
        donation.states.refund(save=True)
        self.assertEqual(Wallpost.objects.count(), 0)

    def test_refund_update_amounts(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        donation = DonationFactory.create(activity=self.funding, amount=Money(250, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(self.funding.amount_raised, Money(750, 'EUR'))
        donation.states.refund(save=True)
        self.assertEqual(self.funding.amount_raised, Money(500, 'EUR'))

    def test_refund_unfollow(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertTrue(self.funding.followers.filter(user=donation.user).exists())
        donation.states.refund(save=True)
        self.assertFalse(self.funding.followers.filter(user=donation.user).exists())

    def test_refund_activity(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, 'succeeded')
        donation.states.activity_refund(save=True)
        self.assertEqual(donation.status, 'activity_refunded')

    def test_refund_activity_payment_request_refund(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = FlutterwavePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        with patch('bluebottle.funding_flutterwave.models.FlutterwavePayment.refund') as refund:
            donation.states.activity_refund(save=True)
            refund.assert_called_once()
        self.assertEqual(payment.status, 'refund_requested')

    def test_refund_activity_mail_supporter(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        mail.outbox = []
        donation.states.activity_refund(save=True)
        self.assertEqual(mail.outbox[0].subject, u'Your donation has been refunded')


class BasePaymentStateMachineTests(BluebottleTestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create()
        bank_account = BankAccountFactory.create(connect_account=payout_account)
        self.funding.bank_account = bank_account
        self.funding.save()
        self.funding.states.approve(save=True)

    def test_initiate(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        self.assertEqual(payment.status, 'new')

    def test_succeed(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(payment.status, 'succeeded')

    def test_succeed_donation_succeed(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(donation.status, 'succeeded')

    def test_fail(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.fail(save=True)
        self.assertEqual(payment.status, 'failed')

    def test_authorize(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.authorize(save=True)
        self.assertEqual(payment.status, 'pending')

    def test_authorize_donation_success(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.authorize(save=True)
        self.assertEqual(donation.status, 'succeeded')

    def test_request_refund(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = FlutterwavePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        with patch('bluebottle.funding_flutterwave.models.FlutterwavePayment.refund'):
            payment.states.request_refund(save=True)
        self.assertEqual(payment.status, 'refund_requested')

    def test_request_refund_call_psp(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = FlutterwavePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        with patch('bluebottle.funding_flutterwave.models.FlutterwavePayment.refund') as refund:
            payment.states.request_refund(save=True)
            refund.assert_called_once()

    def test_refund(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        payment.states.refund(save=True)
        self.assertEqual(payment.status, 'refunded')

    def test_refund_donation_refunded(self):
        donation = DonationFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        payment.states.refund(save=True)
        self.assertEqual(donation.status, 'refunded')
