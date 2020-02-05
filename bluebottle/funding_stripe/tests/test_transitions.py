from datetime import timedelta
import mock

import stripe

from django.utils.timezone import now
from moneyed import Money

from bluebottle.funding_stripe.tests.factories import (
    StripePaymentFactory, StripePayoutAccountFactory, ExternalAccountFactory,
)
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.test.utils import BluebottleTestCase


class StripePaymentTransitionsTestCase(BluebottleTestCase):
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

        donation = DonationFactory.create(
            amount=Money(150, 'EUR'),
            activity=self.funding,
            status='succeeded'
        )

        self.payment = StripePaymentFactory.create(donation=donation)
        super(StripePaymentTransitionsTestCase, self).setUp()

    def test_refund(self):
        self.payment.transitions.succeed()
        payment_intent = stripe.PaymentIntent('some intent id')

        charge = stripe.Charge('charge-id')
        charges = stripe.ListObject()
        charges.data = [charge]

        payment_intent.charges = charges

        with mock.patch('stripe.PaymentIntent.retrieve', return_value=payment_intent):
            with mock.patch('stripe.Charge.refund') as refund_mock:
                self.payment.transitions.request_refund()

        self.assertTrue(refund_mock.called_once)
