import json

from django.urls import reverse

from rest_framework import status
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


class FundingTestCase(BluebottleTestCase):

    def setUp(self):
        super(FundingTestCase, self).setUp()
        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.submit()
        self.initiative.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)

        self.donation_url = reverse('funding-donation-list')
        self.payment_url = reverse('pledge-payment-list')

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
                'type': 'pledge-payments',
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
        response = self.client.post(self.payment_url, data=json.dumps(data), user=self.user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'success')
        self.assertEqual(data['included'][0]['attributes']['status'], 'success')

    def test_create_payment_other_user(self):
        donation_id = self.create_donation()

        data = {
            'data': {
                'type': 'pledge-payments',
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
                'type': 'pledge-payments',
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
