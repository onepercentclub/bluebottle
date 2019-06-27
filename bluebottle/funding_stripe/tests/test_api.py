import json
import mock

from django.urls import reverse

from rest_framework import status

import stripe

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class StripePaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripePaymentTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding, user=self.user)

        self.payment_url = reverse('stripe-payment-list')

        self.data = {
            'data': {
                'type': 'payments/stripe-payments',
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

    def test_create_payment(self):
        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['intent-id'], payment_intent.id)
        self.assertEqual(data['data']['attributes']['client-secret'], payment_intent.client_secret)
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_payment_other_user(self):
        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_payment_no_user(self):
        response = self.client.post(
            self.payment_url,
            data=json.dumps(self.data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
