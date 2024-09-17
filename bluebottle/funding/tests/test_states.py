# -*- coding: utf-8 -*-
from datetime import timedelta
from django.core import mail
from django.utils.timezone import now
from djmoney.money import Money
from mock import patch

from bluebottle.fsm.state import TransitionNotPossible
from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, BankAccountFactory, \
    PlainPayoutAccountFactory, DonorFactory, PayoutFactory
from bluebottle.funding_pledge.tests.factories import PledgePaymentFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentFactory, StripePayoutAccountFactory, \
    ExternalAccountFactory, StripeSourcePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingStateMachineTests(BluebottleTestCase):
    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create(
            account_id="test-account-id", status="verified"
        )
        self.bank_account = ExternalAccountFactory.create(connect_account=payout_account, status='verified')
        self.funding.bank_account = self.bank_account
        self.funding.save()

    def test_submit(self):
        self.funding.states.submit()
        self.assertEqual(self.funding.status, 'submitted')

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

    def test_submit_initiative_not_submitted(self):
        funding = FundingFactory.create(
            target=Money(1000, 'EUR'),
            initiative=InitiativeFactory.create()
        )
        BudgetLineFactory.create(activity=funding)
        funding.bank_account = self.bank_account
        funding.save()

        with self.assertRaisesMessage(TransitionNotPossible, 'Conditions not met for transition'):
            funding.states.submit()

        funding.initiative.states.submit(save=True)
        funding.refresh_from_db()

        self.assertEqual(funding.status, 'submitted')

    def test_submit_missing_budget(self):
        funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        funding.bank_account = self.bank_account
        funding.save()
        with self.assertRaisesMessage(TransitionNotPossible, 'Conditions not met for transition'):
            funding.states.submit()
        self.assertTrue('Please specify a budget' in [er.message for er in funding.errors])

    def test_submit_negative_target(self):
        funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(-1000, 'EUR')
        )
        funding.bank_account = self.bank_account
        funding.save()
        with self.assertRaisesMessage(TransitionNotPossible, 'Conditions not met for transition'):
            funding.states.submit()
        self.assertTrue('Please specify a target' in [er.message for er in funding.errors])

    def test_submit_empty_target(self):
        funding = FundingFactory.create(
            initiative=self.initiative,
            target=None
        )
        funding.bank_account = self.bank_account
        funding.save()
        with self.assertRaisesMessage(TransitionNotPossible, 'Conditions not met for transition'):
            funding.states.submit()
        self.assertTrue('Please specify a target' in [er.message for er in funding.errors])

    def test_empty_target(self):
        funding = FundingFactory.create(
            initiative=self.initiative,
            target=None
        )
        funding.save()
        self.assertFalse(funding.states.target_reached())

    def test_needs_work(self):
        self.funding.states.submit(save=True)
        self.funding.states.request_changes(save=True)
        self.assertEqual(self.funding.status, 'needs_work')

    def test_approve(self):
        self.funding.states.submit()
        mail.outbox = []
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, 'open')

        self.assertEqual(
            mail.outbox[0].subject,
            u'Your campaign "{}" is approved and is now open for donations 💸'.format(
                self.funding.title
            )
        )
        self.assertTrue(
            u'Congratulations! Your campaign “{}” has been approved.'.format(
                self.funding.title
            )
            in mail.outbox[0].body
        )

    def test_cancel(self):
        self.funding.states.submit()
        self.funding.states.approve(save=True)
        mail.outbox = []
        self.funding.states.cancel(save=True)
        self.assertEqual(self.funding.status, 'cancelled')

        self.assertEqual(
            mail.outbox[0].subject,
            u'Your campaign "{}" has been cancelled'.format(
                self.funding.title
            )
        )
        self.assertTrue(
            u'Unfortunately your campaign “{}” has been cancelled.'.format(
                self.funding.title
            )
            in mail.outbox[0].body
        )

    def test_approve_organizer_succeed(self):
        self.funding.states.submit()
        self.funding.states.approve(save=True)
        organizer = self.funding.contributors.get()
        self.assertEqual(organizer.status, 'succeeded')

    def test_approve_set_start_dat(self):
        self.funding.states.submit()
        self.funding.states.approve(save=True)
        organizer = self.funding.contributors.get()
        self.assertEqual(organizer.status, 'succeeded')

    def test_approve_set_deadline(self):
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR'),
            deadline=None,
            duration=7
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = PlainPayoutAccountFactory.create(status="verified")
        bank_account = BankAccountFactory.create(
            connect_account=payout_account, status="verified"
        )
        self.funding.bank_account = bank_account
        self.funding.save()

        self.funding.states.submit()
        self.funding.states.approve(save=True)
        next_week = now() + timedelta(days=7)
        self.assertEqual(self.funding.deadline.date(), next_week.date())

    def test_approve_should_close(self):
        self.funding.deadline = now() - timedelta(days=5)
        self.funding.states.submit()
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, 'cancelled')

    def _prepare_extend(self):
        self.funding.states.submit()
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, 'open')
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        # Changing the deadline to the past should trigger a transition
        self.funding.deadline = now() - timedelta(days=1)
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'partially_funded')

    def test_extend(self):
        self._prepare_extend()
        # Changing the deadline to the future should open the campaign again
        mail.outbox = []
        self.funding.deadline = now() + timedelta(days=7)
        self.funding.save()
        self.funding.refresh_from_db()
        self.assertEqual(self.funding.status, 'open')
        self.assertEqual(
            mail.outbox[0].recipients(),
            [self.funding.owner.email]
        )

        self.assertEqual(
            mail.outbox[0].subject,
            u'Your campaign "{}" is open for new donations 💸'.format(
                self.funding.title
            )
        )

        self.assertTrue(
            u'The deadline for your campaign “{}” has been extended.'.format(
                self.funding.title
            ) in mail.outbox[0].body
        )

    def test_extend_delete_payouts(self):
        self._prepare_extend()
        self.assertEqual(self.funding.payouts.count(), 1)
        # Changing the deadline to the future should open the campaign again
        self.funding.deadline = now() + timedelta(days=7)
        self.funding.save()
        self.assertEqual(self.funding.payouts.count(), 0)

    def test_delete(self):
        self.funding.states.delete(save=True)
        self.assertEqual(self.funding.status, 'deleted')
        organizer = self.funding.contributors.get()
        self.assertEqual(organizer.status, 'failed')

    def _prepare_succeeded(self):
        self.funding.states.submit()
        self.funding.states.approve(save=True)
        self.assertEqual(self.funding.status, 'open')
        donation = DonorFactory.create(activity=self.funding, amount=Money(1000, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.funding.deadline = now() - timedelta(days=1)

    def test_succeed(self):
        self._prepare_succeeded()
        self.funding.states.succeed(save=True)
        self.assertEqual(self.funding.status, 'succeeded')

    def test_refund(self):
        self._prepare_succeeded()
        self.funding.states.succeed(save=True)
        mail.outbox = []
        self.funding.states.refund(save=True)
        self.assertEqual(self.funding.status, 'refunded')

        donor_mail = [
            message for message in mail.outbox if
            self.funding.donations.get().user.email in message.recipients()
        ][0]

        self.assertEqual(
            donor_mail.subject,
            u'Your donation for the campaign "{}" will be refunded'.format(
                self.funding.title
            )
        )

        self.assertTrue(
            'Unfortunately, the campaign "{}" did not reach its goal'.format(
                self.funding.title
            ) in donor_mail.body
        )

        owner_mail = [
            message for message in mail.outbox if
            self.funding.owner.email in message.recipients()
        ][0]

        self.assertEqual(
            owner_mail.subject,
            u'The donations received for your campaign "{}" will be refunded'.format(
                self.funding.title
            )
        )

        self.assertTrue(
            'All donations received for your campaign "{}" will be refunded to the donors.'.format(
                self.funding.title
            ) in owner_mail.body
        )

    def test_succeed_owner_message(self):
        self._prepare_succeeded()
        mail.outbox = []
        self.funding.states.succeed(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'Your campaign "{}" has been successfully completed! \U0001f389'.format(self.funding.title)
        )

    def test_succeed_generate_payouts(self):
        self._prepare_succeeded()
        self.funding.states.succeed(save=True)
        self.assertEqual(self.funding.status, 'succeeded')
        self.assertEqual(self.funding.payouts.count(), 1)
        self.assertEqual(self.funding.payouts.first().total_amount, Money(1000, 'EUR'))

    def test_reject(self):
        mail.outbox = []
        self.funding.states.submit()
        self.funding.states.reject(save=True)
        self.assertEqual(self.funding.status, 'rejected')
        organizer = self.funding.contributors.get()
        self.assertEqual(organizer.status, 'failed')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            u'Your crowdfunding campaign has been rejected.'
        )

    def test_close_with_donations(self):
        mail.outbox = []
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        with self.assertRaisesMessage(
                TransitionNotPossible,
                'Conditions not met for transition'):
            self.funding.states.reject(save=True)


class DonationStateMachineTests(BluebottleTestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create(
            account_id="test-account-id", status="verified"
        )
        bank_account = ExternalAccountFactory.create(connect_account=payout_account, status='verified')
        self.funding.bank_account = bank_account
        self.funding.save()
        self.funding.states.submit()
        self.funding.states.approve(save=True)

    def test_initiate(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        self.assertEqual(donation.status, 'new')

    def test_succeed(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(donation.status, 'succeeded')

        money_contribution = donation.contributions.get()
        self.assertEqual(
            money_contribution.status,
            'succeeded'
        )
        self.assertAlmostEqual(
            money_contribution.start,
            now(),
            delta=timedelta(minutes=2)
        )

    def test_succeed_update_amounts(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(self.funding.amount_raised, Money(500, 'EUR'))

    def test_succeed_mail_supporter(self):
        mail.outbox = []
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(mail.outbox[0].subject, u'You have a new donation!\U0001f4b0')

    def test_succeed_mail_activity_manager(self):
        mail.outbox = []
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(mail.outbox[1].subject, u'Thanks for your donation!')

    def test_succeed_follow(self):
        mail.outbox = []
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        self.assertTrue(self.funding.followers.filter(user=donation.user).exists())

    def test_fail(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.fail(save=True)
        self.assertEqual(donation.status, 'failed')

    def test_fail_update_amounts(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        donation.states.succeed(save=True)
        donation = DonorFactory.create(activity=self.funding, amount=Money(250, 'EUR'))
        donation.states.succeed(save=True)
        self.assertEqual(self.funding.amount_raised, Money(750, 'EUR'))
        donation.states.fail(save=True)
        self.assertEqual(self.funding.amount_raised, Money(500, 'EUR'))

    def test_refund(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, 'succeeded')

        mail.outbox = []
        donation.payment.states.refund(save=True)
        self.assertEqual(donation.status, 'refunded')

        self.assertEqual(
            mail.outbox[0].recipients(),
            [donation.user.email]
        )

        self.assertEqual(
            mail.outbox[0].subject,
            u'Your donation for the campaign "{}" will be refunded'.format(
                self.funding.title
            )
        )

        self.assertTrue(
            'Your donation to "{}" will be fully refunded within 10 days.'.format(
                self.funding.title
            ) in mail.outbox[0].body
        )

    def test_refund_payment_request_refund(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.funding.states.succeed(save=True)
        with patch('bluebottle.funding_stripe.models.StripeSourcePayment.refund') as refund:
            payment.states.request_refund(save=True)
            refund.asssert_called_once()
        self.assertEqual(payment.status, 'refund_requested')

    def test_refund_update_amounts(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        donation = DonorFactory.create(activity=self.funding, amount=Money(250, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(self.funding.amount_raised, Money(750, 'EUR'))
        donation.payment.states.refund(save=True)
        self.assertEqual(self.funding.amount_raised, Money(500, 'EUR'))

    def test_refund_unfollow(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)

        self.assertTrue(self.funding.followers.filter(user=donation.user).exists())
        donation.payment.states.refund(save=True)
        self.assertFalse(self.funding.followers.filter(user=donation.user).exists())

    def test_refund_activity(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        self.assertEqual(donation.status, 'succeeded')
        donation.states.activity_refund(save=True)
        self.assertEqual(donation.status, 'activity_refunded')

    def test_refund_activity_payment_request_refund(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.funding.states.succeed(save=True)
        with patch('bluebottle.funding_stripe.models.StripeSourcePayment.refund') as refund:
            self.funding.states.refund(save=True)

            refund.assert_called_once()

        payment.refresh_from_db()
        self.assertEqual(payment.status, 'refund_requested')

    def test_refund_activity_mail_supporter(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        PledgePaymentFactory.create(donation=donation)
        mail.outbox = []
        donation.states.activity_refund(save=True)
        self.assertEqual(
            mail.outbox[0].subject,
            u'Your donation for the campaign "{}" will be refunded'.format(self.funding.title)
        )


class BasePaymentStateMachineTests(BluebottleTestCase):

    def setUp(self):
        self.initiative = InitiativeFactory.create()
        self.initiative.states.submit()
        self.initiative.states.approve(save=True)
        self.funding = FundingFactory.create(
            initiative=self.initiative,
            target=Money(1000, 'EUR')
        )
        BudgetLineFactory.create(activity=self.funding)
        payout_account = StripePayoutAccountFactory.create(
            account_id="test-account-id", status="verified"
        )
        bank_account = ExternalAccountFactory.create(connect_account=payout_account, status='verified')
        self.funding.bank_account = bank_account
        self.funding.states.submit()
        self.funding.states.approve(save=True)

    def test_initiate(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        self.assertEqual(payment.status, 'new')

    def test_succeed(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(payment.status, 'succeeded')

    def test_succeed_donation_succeed(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(donation.status, 'succeeded')

    def test_fail(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.fail(save=True)
        self.assertEqual(payment.status, 'failed')

    def test_authorize(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.authorize(save=True)
        self.assertEqual(payment.status, 'pending')

    def test_authorize_donation_success(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.authorize(save=True)
        self.assertEqual(donation.status, 'succeeded')

    def test_request_refund(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        with patch('bluebottle.funding_stripe.models.StripeSourcePayment.refund') as refund:
            payment.states.request_refund(save=True)
            refund.assert_called_once()
        self.assertEqual(payment.status, 'refund_requested')

    def test_refund(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        payment.states.refund(save=True)
        self.assertEqual(payment.status, 'refunded')

    def test_refund_donation_refunded(self):
        donation = DonorFactory.create(activity=self.funding, amount=Money(500, 'EUR'))
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        payment.states.refund(save=True)
        self.assertEqual(donation.status, 'refunded')


class PlainPayoutAccountStateMachineTests(BluebottleTestCase):

    def setUp(self):
        self.account = PlainPayoutAccountFactory.create()

    def test_initial(self):
        self.assertEqual(self.account.status, 'new')

    def test_accept(self):
        self.account.states.verify(save=True)
        self.assertEqual(self.account.status, 'verified')

    def test_accept_mail(self):
        self.account.states.verify(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your identity has been verified')

    def test_reject(self):
        self.account.states.reject(save=True)
        self.assertEqual(self.account.status, 'rejected')

    def test_reject_mail(self):
        self.account.states.reject(save=True)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Your identity verification could not be verified!')


class PayoutStateMachineTests(BluebottleTestCase):

    def setUp(self):
        self.payout = PayoutFactory.create()

    def test_initial(self):
        self.assertEqual(self.payout.status, 'new')

    @patch('bluebottle.payouts_dorado.adapters.DoradoPayoutAdapter.trigger_payout')
    def test_accept(self, mock_trigger_payout):
        self.payout.states.approve(save=True)
        self.assertEqual(self.payout.status, 'approved')

    @patch('bluebottle.payouts_dorado.adapters.DoradoPayoutAdapter.trigger_payout')
    def test_accept_date_set(self, mock_trigger_payout):
        self.payout.states.approve(save=True)
        self.assertAlmostEqual(self.payout.date_approved, now(), delta=timedelta(seconds=60))

    @patch('bluebottle.payouts_dorado.adapters.DoradoPayoutAdapter.trigger_payout')
    def test_accept_adapter_called(self, mock_trigger_payout):
        self.payout.states.approve(save=True)
        mock_trigger_payout.assert_called_once()

    def test_start(self):
        self.payout.states.start(save=True)
        self.assertEqual(self.payout.status, 'started')

    def test_start_date_set(self):
        self.payout.states.start(save=True)
        self.assertAlmostEqual(self.payout.date_started, now(), delta=timedelta(seconds=60))

    def test_succeed(self):
        self.payout.states.succeed(save=True)
        self.assertEqual(self.payout.status, 'succeeded')

    def test_succeed_date_set(self):
        self.payout.states.succeed(save=True)
        self.assertAlmostEqual(self.payout.date_completed, now(), delta=timedelta(seconds=60))

    def test_reset(self):
        self.payout.states.succeed(save=True)
        self.payout.states.reset(save=True)
        self.assertEqual(self.payout.status, 'new')

    @patch('bluebottle.payouts_dorado.adapters.DoradoPayoutAdapter.trigger_payout')
    def test_reset_dates_cleared(self, mock_trigger_payout):
        self.payout.states.approve(save=True)
        self.payout.states.start(save=True)
        self.payout.states.succeed(save=True)
        self.payout.states.reset(save=True)
        self.assertIsNone(self.payout.date_approved)
        self.assertIsNone(self.payout.date_started)
        self.assertIsNone(self.payout.date_completed)
