from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from rest_framework.status import HTTP_200_OK

from bluebottle.funding_flutterwave.tests.factories import FlutterwavePaymentFactory, FlutterwavePaymentProviderFactory
from bluebottle.test.utils import BluebottleTestCase

flutterwave_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'flutterwave',
            'currency': 'NGN',
            'pub_key': '123456789123456789',
            'sec_key': '123456789123456789',
        },
    ]
}

success_response = {
    'status': 'success',
    'data': {}
}


@override_settings(**flutterwave_settings)
class FlutterwaveWebhookTest(BluebottleTestCase):

    def setUp(self):
        super(FlutterwaveWebhookTest, self).setUp()
        FlutterwavePaymentProviderFactory.create()
        self.webhook_url = reverse('flutterwave-payment-webhook')
        self.payment = FlutterwavePaymentFactory.create(tx_ref='bla-di-bla')

    @patch('bluebottle.funding_flutterwave.utils.post',
           return_value=success_response)
    def test_webhook(self, mock_post):
        payload = {
            "id": 1231,
            "txRef": self.payment.tx_ref,
            "flwRef": "FLW-MOCK-3aa21c8ed962e5b64a986403fc60fa2d",
            "amount": 17500,
            "currency": "NGN",
            "customer": {
                "id": 154159,
            },
            "event.type": "CARD_TRANSACTION"
        }

        response = self.client.post(self.webhook_url, data=payload)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.payment.refresh_from_db()
        donation = self.payment.donation
        donation.refresh_from_db()
        self.assertEqual(self.payment.status, 'success')
        self.assertEqual(donation.status, 'success')

    @classmethod
    def setUpClass(cls):
        super(FlutterwaveWebhookTest, cls).setUpClass()
