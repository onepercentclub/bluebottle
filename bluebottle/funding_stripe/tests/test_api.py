import json
import mock

from django.urls import reverse

from rest_framework import status

import stripe

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_stripe.tests.factories import StripePaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class StripePaymentIntentTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripePaymentIntentTestCase, self).setUp()
        StripePaymentProviderFactory.create()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding, user=None)

        self.intent_url = reverse('stripe-payment-intent-list')

        self.data = {
            'data': {
                'type': 'payments/stripe-payment-intents',
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'contributions/donations',
                            'id': self.donation.pk,
                        }
                    }
                }
            }
        }

    def test_create_intent(self):
        self.donation.user = self.user
        self.donation.save()

        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(self.intent_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['intent-id'], payment_intent.id)
        self.assertEqual(data['data']['attributes']['client-secret'], payment_intent.client_secret)
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_intent_anonymous(self):
        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(
                self.intent_url,
                data=json.dumps(self.data),
                HTTP_AUTHORIZATION='Donation {}'.format(self.donation.client_secret)
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['intent-id'], payment_intent.id)
        self.assertEqual(data['data']['attributes']['client-secret'], payment_intent.client_secret)
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_intent_wrong_token(self):
        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(
                self.intent_url,
                data=json.dumps(self.data),
                HTTP_AUTHORIZATION='Donation wrong-token'
            )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_intent_other_user(self):
        self.donation.user = self.user
        self.donation.save()

        response = self.client.post(
            self.intent_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_intent_no_user(self):
        response = self.client.post(
            self.intent_url,
            data=json.dumps(self.data),
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
