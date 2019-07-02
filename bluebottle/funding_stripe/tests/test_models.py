import mock

import stripe

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_stripe.transitions import StripePaymentTransitions
from bluebottle.funding_stripe.models import StripePayment
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class StripePaymentTestCase(BluebottleTestCase):
    def setUp(self):
        super(StripePaymentTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)

        self.payment_intent = stripe.PaymentIntent('some intent id')
        self.payment_intent.update({
            'client_secret': 'some client secret',
            'charges': [stripe.Charge('some charge id')]
        })

    def test_create(self):
        payment = StripePayment(donation=self.donation)

        with mock.patch('stripe.PaymentIntent.create', return_value=self.payment_intent):
            payment.save()

        self.assertEqual(payment.intent_id, self.payment_intent.id)
        self.assertEqual(payment.client_secret, self.payment_intent.client_secret)
        self.assertEqual(payment.status, StripePaymentTransitions.values.new)

    def test_refund(self):
        payment = StripePayment(donation=self.donation)
        payment.transitions.succeed()

        with mock.patch('stripe.PaymentIntent.create', return_value=self.payment_intent):
            payment.save()

        with mock.patch('stripe.PaymentIntent.retrieve', return_value=self.payment_intent):
            with mock.patch('stripe.Charge.refund', return_value=self.payment_intent.charges[0]):
                payment.transitions.request_refund()

        self.assertEqual(payment.status, StripePaymentTransitions.values.refund_requested)
