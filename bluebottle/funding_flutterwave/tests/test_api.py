import json

from django.urls import reverse
from mock import patch
from rest_framework import status

from bluebottle.funding.tests.factories import FundingFactory, DonationFactory
from bluebottle.funding.transitions import DonationTransitions, PaymentTransitions
from bluebottle.funding_flutterwave.tests.factories import FlutterwavePaymentProviderFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase, JSONAPITestClient

success_response = {
    'status': 'success',
    'data': {
        'status': 'successful'
    }
}

failed_response = {
    'status': 'success',
    'data': {
        'status': 'failed'
    }
}


class FlutterwavePaymentTestCase(BluebottleTestCase):

    def setUp(self):
        super(FlutterwavePaymentTestCase, self).setUp()
        provider = FlutterwavePaymentProviderFactory.create()

        self.client = JSONAPITestClient()
        self.user = BlueBottleUserFactory()
        self.initiative = InitiativeFactory.create()

        self.initiative.transitions.submit()
        self.initiative.transitions.approve()
        self.funding = FundingFactory.create(initiative=self.initiative)
        self.donation = DonationFactory.create(activity=self.funding, user=self.user)

        self.payment_url = reverse('flutterwave-payment-list')

        self.tx_ref = "{}-{}".format(provider.prefix, self.donation.id)

        self.data = {
            'data': {
                'type': 'payments/flutterwave-payments',
                'attributes': {
                    'tx-ref': self.tx_ref
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

    @patch('bluebottle.funding_flutterwave.utils.post', return_value=success_response)
    def test_create_payment_success(self, flutterwave_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], PaymentTransitions.values.succeeded)
        self.assertEqual(data['data']['attributes']['tx-ref'], self.tx_ref)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationTransitions.values.succeeded)

    @patch('bluebottle.funding_flutterwave.utils.post', return_value=failed_response)
    def test_create_payment_failure(self, flutterwave_post):
        response = self.client.post(self.payment_url, data=json.dumps(self.data), user=self.user)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = json.loads(response.content)

        self.assertEqual(data['data']['attributes']['status'], PaymentTransitions.values.failed)
        self.assertEqual(data['data']['attributes']['tx-ref'], self.tx_ref)
        self.donation.refresh_from_db()
        self.assertEqual(self.donation.status, DonationTransitions.values.failed)
