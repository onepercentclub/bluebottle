import json
import mock


from django.urls import reverse

from rest_framework import status

import stripe

from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class StripePaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(StripePaymentTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.submit()
        self.initiative.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)

        self.donation_url = reverse('funding-donation-list')
        self.payment_url = reverse('stripe-payment-list')

    def create_donation(self):
        data = {
            'data': {
                'type': 'donations',
                'attributes': {
                    'amount': {'currency': 'EUR', 'amount': 100},
                },
                'relationships': {
                    'activity': {
                        'data': {
                            'type': 'activities/funding',
                            'id': self.funding.pk
                        }
                    }
                }
            }
        }

        response = self.client.post(self.donation_url, data=json.dumps(data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        return data['data']['id']

    def test_create_payment(self):
        donation_id = self.create_donation()

        data = {
            'data': {
                'type': 'stripe-payments',
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'donations',
                            'id': donation_id,
                        }
                    }
                }
            }
        }

        payment_intent = stripe.PaymentIntent('some intent id')
        payment_intent.update({
            'client_secret': 'some client secret',
        })

        with mock.patch('stripe.PaymentIntent.create', return_value=payment_intent):
            response = self.client.post(self.payment_url, data=json.dumps(data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['intent-id'], payment_intent.id)
        self.assertEqual(data['data']['attributes']['client-secret'], payment_intent.client_secret)
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    def test_create_payment_other_user(self):
        donation_id = self.create_donation()

        data = {
            'data': {
                'type': 'stripe-payments',
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'donations',
                            'id': donation_id,
                        }
                    }
                }
            }
        }
        response = self.client.post(
            self.payment_url,
            data=json.dumps(data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_payment_no_user(self):
        donation_id = self.create_donation()

        data = {
            'data': {
                'type': 'stripe-payments',
                'relationships': {
                    'donation': {
                        'data': {
                            'type': 'donations',
                            'id': donation_id,
                        }
                    }
                }
            }
        }
        response = self.client.post(
            self.payment_url,
            data=json.dumps(data),
            user=BlueBottleUserFactory.create()
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
