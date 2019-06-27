import json
import mock

import bunch

from django.urls import reverse

from rest_framework import status

import stripe

from bluebottle.funding.models import Donation
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentFactory
from bluebottle.funding_stripe.models import StripePayment
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class MockEvent(object):
    def __init__(self, type, data):
        self.type = type
        self.data = bunch.bunchify(data)


class StripePaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripePaymentTestCase, self).setUp()
        self.initiative = InitiativeFactory.create()

        self.initiative.submit()
        self.initiative.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)

        self.payment_intent = stripe.PaymentIntent('some intent id')
        self.payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=self.payment_intent):
            self.payment = StripePaymentFactory.create(donation=self.donation)

        self.webhook = reverse('stripe-payment-webhook')

    def test_success(self):
        with open('bluebottle/funding_stripe/tests/files/intent_webhook_success.json') as hook_file:
            data = json.load(hook_file)
            data['object']['id'] = self.payment_intent.id

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.succeeded', data
            )
        ):
            response = self.client.post(
                reverse('stripe-payment-webhook'),
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment = StripePayment.objects.get(pk=self.payment.pk)
        donation = Donation.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, Donation.Status.success)
        self.assertEqual(payment.status, StripePayment.Status.success)

    def test_failed(self):
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.payment_failed', {'object': {'id': self.payment_intent.id}}
            )
        ):
            response = self.client.post(
                reverse('stripe-payment-webhook'),
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment = StripePayment.objects.get(pk=self.payment.pk)
        donation = Donation.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, Donation.Status.failed)
        self.assertEqual(payment.status, StripePayment.Status.failed)

    def test_refund(self):
        with open('bluebottle/funding_stripe/tests/files/intent_webhook_refund.json') as hook_file:
            data = json.load(hook_file)
            data['object']['payment_intent'] = self.payment_intent.id

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.refunded', data
            )
        ):
            response = self.client.post(
                reverse('stripe-payment-webhook'),
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        payment = StripePayment.objects.get(pk=self.payment.pk)
        donation = Donation.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, Donation.Status.refunded)
        self.assertEqual(payment.status, StripePayment.Status.refunded)

    def test_no_payment(self):
        pass

    def test_wrong_signature(self):
        pass

    def test_no_signature(self):
        pass
