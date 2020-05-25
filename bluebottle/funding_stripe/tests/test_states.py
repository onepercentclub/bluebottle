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
    def setUp(self, mock_modify):
        super(StripeSourcePaymentStateMachineTests, self).setUp()
        self.donation = DonationFactory.create(activity=self.funding)
        self.payment = StripeSourcePaymentFactory.create(
            charge_token='some_token',
            donation=self.donation
        )

    def test_request_refund(self):
        self.payment.states.succeed(save=True)
        self.assertEqual(self.payment.status, 'succeeded')
        with patch('bluebottle.funding_stripe.models.StripeSourcePayment.refund') as refund:
            self.payment.states.request_refund(save=True)
            refund.assert_called_once()
            self.assertEqual(self.payment.status, 'refund_requested')

    def test_authorize(self):
        self.payment.states.charge(save=True)
        self.payment.states.authorize(save=True)
        self.assertEqual(self.payment.status, 'pending')

    def test_authorize_donation_succeed(self):
        self.payment.states.charge(save=True)
        self.payment.states.authorize(save=True)
        self.assertEqual(self.donation.status, 'succeeded')

    def test_succeed(self):
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)
        self.assertEqual(self.payment.status, 'succeeded')

    def test_succeed_donation_succeed(self):
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)
        self.assertEqual(self.donation.status, 'succeeded')

    def test_charge(self):
        self.payment.states.charge(save=True)
        self.assertEqual(self.payment.status, 'charged')

    def test_cancel(self):
        self.payment.states.cancel(save=True)
        self.assertEqual(self.payment.status, 'canceled')

    def test_dispute(self):
        self.payment.states.charge(save=True)
        self.payment.states.succeed(save=True)
        self.payment.states.dispute(save=True)
        self.assertEqual(self.payment.status, 'disputed')


class StripePaymentStateMachineTests(BaseStripePaymentStateMachineTests):

    @patch('stripe.PaymentIntent.retrieve')
    def test_request_refund(self, mock_retrieve):
        donation = DonationFactory.create(activity=self.funding)
        payment = StripePaymentFactory.create(donation=donation)
        payment.states.succeed(save=True)
        self.assertEqual(payment.status, 'succeeded')
        payment.states.request_refund(save=True)
        self.assertEqual(payment.status, 'refund_requested')
