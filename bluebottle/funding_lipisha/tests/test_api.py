import json

from django.urls import reverse
from mock import patch
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding_lipisha.models import LipishaPaymentProvider
from bluebottle.funding_lipisha.tests.factories import LipishaPaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient


initiate_response_fail = {
    "status": {
        "status": "FAIL",
        "status_code": "3000",
        "status_description": "Invalid API Credentials"
    },
    "content": []
}

initiate_response_success = {
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
        LipishaPaymentProvider.objects.all().delete()
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

    @patch('lipisha.Lipisha._make_api_call', return_value=initiate_response_success)
    def test_create_payment(self, lipisha_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], 'new')
        self.assertEqual(data['data']['attributes']['transaction'], 'ABC12345QR')
        self.assertEqual(data['included'][0]['attributes']['status'], 'new')

    @patch('lipisha.Lipisha._make_api_call', return_value=initiate_response_fail)
    def test_create_payment_fail(self, lipisha_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.content, "Error creating payment: Invalid API Credentials")
