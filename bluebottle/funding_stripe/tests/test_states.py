from djmoney.money import Money
from mock import patch

from bluebottle.funding.tests.factories import FundingFactory, BudgetLineFactory, BankAccountFactory, DonationFactory
from bluebottle.funding_stripe.tests.factories import StripePayoutAccountFactory, StripeSourcePaymentFactory, \
    StripePaymentFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class BaseStripePaymentStateMachineTests(BluebottleTestCase):
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


class StripeSourcePaymentStateMachineTests(BaseStripePaymentStateMachineTests):

    @patch('stripe.Source.modify')
    def test_request_refund(self, mock_modify):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(payment.status, 'succeeded')
        with patch('bluebottle.funding_stripe.models.StripeSourcePayment.refund') as refund:
            payment.states.request_refund(save=True)
            refund.assert_called_once()
            self.assertEqual(payment.status, 'refund_requested')

    def test_authorize(self):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.authorize(save=True)
        self.assertEqual(payment.status, 'pending')

    def test_authorize_donation_succeed(self):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.authorize(save=True)
        self.assertEqual(donation.status, 'succeeded')

    def test_succeed(self):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(payment.status, 'succeeded')

    def test_succeed_donation_succeed(self):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(donation.status, 'succeeded')

    def test_charge(self):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.charge(save=True)
        self.assertEqual(payment.status, 'charged')

    def test_cancel(self):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.cancel(save=True)
        self.assertEqual(payment.status, 'canceled')

    def test_dispute(self):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripeSourcePaymentFactory.create(donation=donation)
        payment.states.dispute(save=True)
        self.assertEqual(payment.status, 'disputed')


class StripePaymentStateMachineTests(BaseStripePaymentStateMachineTests):

    @patch('stripe.PaymentIntent.retrieve')
    def test_request_refund(self, mock_retrieve):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(payment.status, 'succeeded')
        payment.states.request_refund(save=True)
        self.assertEqual(payment.status, 'refund_requested')
