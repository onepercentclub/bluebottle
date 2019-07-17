import json

from django.urls import reverse
from mock import patch
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_lipisha.tests.factories import LipishaPaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient

initiate_response = {
    "status": {
        "status_code": "0000",
        "status_description": "Payment Requested",
        "status": "SUCCESS"
    },
    "content": {
        "transaction": "ABC12345QR",
        "method": "Paybill (M-Pesa)",
        "account_number": "00100",
        "mobile_number": "254712345678",
        "amount": "1000",
        "currency": "KES",
        "reference": "INV000001"
    }
}


class LipishaPaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(LipishaPaymentTestCase, self).setUp()
        LipishaPaymentProviderFactory.create()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()

        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding, user=self.user)

        self.payment_url = reverse('lipisha-payment-list')

        self.data = {
            'data': {
                'type': 'payments/lipisha-payments',
                'attributes': {
                },
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

    @patch('bluebottle.funding.adapters.requests.post',
           return_value=type('obj', (object,),
                             {'status_code': 200, 'content': 'https://lipisha.com/some-path-to-pay'}))
    def test_create_payment(self, lipisha_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['payment-url'], 'https://lipisha.com/some-path-to-pay')
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')
