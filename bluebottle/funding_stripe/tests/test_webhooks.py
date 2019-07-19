import json
import mock

import bunch

from django.urls import reverse

from rest_framework import status

import stripe

from bluebottle.funding.models import Donation
from bluebottle.funding.transitions import DonationTransitions
from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_stripe.tests.factories import (
    StripePaymentIntentFactory,
    StripePaymentProviderFactory,
    StripeSourcePaymentFactory
)
from bluebottle.funding_stripe.transitions import StripePaymentTransitions, StripeSourcePaymentTransitions
from bluebottle.funding_stripe.models import StripeSourcePayment
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.utils import BluebottleTestCase


class MockEvent(object):
    def __init__(self, type, data):
        self.type = type
        self.data = bunch.bunchify(data)


class IntentWebhookTestCase(BluebottleTestCase):

    def setUp(self):
        super(IntentWebhookTestCase, self).setUp()
        StripePaymentProviderFactory.create()
        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)

        self.payment_intent = stripe.PaymentIntent('some intent id')
        self.payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=self.payment_intent):
            self.intent = StripePaymentIntentFactory.create(donation=self.donation)

        self.webhook = reverse('stripe-intent-webhook')

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
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.intent.refresh_from_db()
        payment = self.intent.payment
        donation = Donation.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, DonationTransitions.values.succeeded)
        self.assertEqual(payment.status, StripePaymentTransitions.values.succeeded)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationTransitions.values.succeeded)

    def test_failed(self):
        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'payment_intent.payment_failed', {'object': {'id': self.payment_intent.id}}
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.intent.refresh_from_db()
        payment = self.intent.payment

        donation = Donation.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, DonationTransitions.values.failed)
        self.assertEqual(payment.status, StripePaymentTransitions.values.failed)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationTransitions.values.failed)

    def test_refund(self):
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
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

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
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.intent.refresh_from_db()
        payment = self.intent.payment

        donation = Donation.objects.get(pk=self.donation.pk)

        self.assertEqual(donation.status, DonationTransitions.values.refunded)
        self.assertEqual(payment.status, StripePaymentTransitions.values.refunded)


class SourcePaymentWebhookTestCase(BluebottleTestCase):
    def setUp(self):
        super(SourcePaymentWebhookTestCase, self).setUp()
        StripePaymentProviderFactory.create()

        self.initiative = InitiativeFactory.create()
        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding)

        self.payment = StripeSourcePaymentFactory.create(
            source_token='some-source-id',
            donation=self.donation
        )

        self.webhook = reverse('stripe-source-webhook')

    def _refresh(self):
        self.donation = Donation.objects.get(pk=self.donation.pk)
        self.payment = StripeSourcePayment.objects.get(pk=self.payment.pk)

    def test_source_failed(self):
        data = {
            'object': {
                'id': self.payment.source_token
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'source.failed', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, DonationTransitions.values.failed)
        self.assertEqual(self.payment.status, StripeSourcePaymentTransitions.values.failed)

    def test_source_canceled(self):
        data = {
            'object': {
                'id': self.payment.source_token
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'source.canceled', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, DonationTransitions.values.failed)
        self.assertEqual(self.payment.status, StripeSourcePaymentTransitions.values.canceled)

    def test_source_chargeable(self):
        data = {
            'object': {
                'id': self.payment.source_token
            }
        }
        charge = stripe.Charge('some charge token')
        charge.update({
            'status': 'succeeded',
            'refunded': False
        })

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'source.chargeable', data
            )
        ):
            with mock.patch('stripe.Charge.create', return_value=charge):
                response = self.client.post(
                    self.webhook,
                    HTTP_STRIPE_SIGNATURE='some signature'
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, DonationTransitions.values.new)
        self.assertEqual(self.payment.status, StripeSourcePaymentTransitions.values.charged)

    def test_charge_succeeded(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.transitions.charge()
        self.payment.save()

        data = {
            'object': {
                'id': self.payment.charge_token
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.succeeded', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, DonationTransitions.values.succeeded)
        self.assertEqual(self.payment.status, StripeSourcePaymentTransitions.values.succeeded)

    def test_charge_failed(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.transitions.charge()
        self.payment.save()

        data = {
            'object': {
                'id': self.payment.charge_token
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.failed', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, DonationTransitions.values.failed)
        self.assertEqual(self.payment.status, StripeSourcePaymentTransitions.values.failed)

    def test_charge_refunded(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.transitions.charge()
        self.payment.transitions.succeed()
        self.payment.save()

        data = {
            'object': {
                'id': self.payment.charge_token
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.refunded', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, DonationTransitions.values.refunded)
        self.assertEqual(self.payment.status, StripeSourcePaymentTransitions.values.refunded)

    def test_charge_dispute_closed(self):
        self.payment.charge_token = 'some-charge-token'
        self.payment.transitions.charge()
        self.payment.transitions.succeed()
        self.payment.save()

        data = {
            'object': {
                'charge': self.payment.charge_token,
                'status': 'lost'
            }
        }

        with mock.patch(
            'stripe.Webhook.construct_event',
            return_value=MockEvent(
                'charge.dispute.closed', data
            )
        ):
            response = self.client.post(
                self.webhook,
                HTTP_STRIPE_SIGNATURE='some signature'
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self._refresh()
        self.assertEqual(self.donation.status, DonationTransitions.values.refunded)
        self.assertEqual(self.payment.status, StripeSourcePaymentTransitions.values.disputed)
