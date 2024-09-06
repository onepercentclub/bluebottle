import mock
import stripe
from moneyed import Money

from bluebottle.funding.tests.factories import FundingFactory, DonorFactory, BudgetLineFactory
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentFactory, StripePayoutAccountFactory, ExternalAccountFactory,
)
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class StripePaymentTransitionsTestCase(BluebottleTestCase):
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

        donation = DonorFactory.create(
            amount=Money(150, 'EUR'),
            activity=self.funding,
            status='succeeded'
        )

        self.payment = StripePaymentFactory.create(donation=donation)
        super(StripePaymentTransitionsTestCase, self).setUp()

    def test_refund(self):
        self.payment.states.succeed(save=True)
        payment_intent = stripe.PaymentIntent('some intent id')

        charge = stripe.Charge('charge-id')
        charges = stripe.ListObject()
        charges.data = [charge]

        payment_intent.charges = charges

        with mock.patch("stripe.PaymentIntent.retrieve", return_value=payment_intent):
            with mock.patch("stripe.Refund.create") as refund_mock:
                self.payment.states.request_refund(save=True)

        self.assertTrue(refund_mock.called_once)
