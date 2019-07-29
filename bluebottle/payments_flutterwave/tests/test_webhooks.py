from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from rest_framework.status import HTTP_200_OK

from bluebottle.payments.models import OrderPayment
from bluebottle.payments_flutterwave.tests.factory_models import (
    FlutterwavePaymentFactory)
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
    'data': {
        'status': 'successful'
    }
}


@override_settings(**flutterwave_settings)
class FlutterwaveWebhookTest(BluebottleTestCase):

    def setUp(self):
        super(FlutterwaveWebhookTest, self).setUp()
        self.webhook_url = reverse('flutterwave-webhook')
        self.payment = FlutterwavePaymentFactory.create()
        self.payment.transaction_reference = self.payment.order_payment.order.id
        self.payment.save()

    @patch('bluebottle.payments_flutterwave.adapters.FlutterwaveCreditcardPaymentAdapter.post',
           return_value=success_response)
    def test_webhook(self, mock_post):
        payload = {
            "id": 1231,
            "txRef": self.payment.transaction_reference,
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
        order_payment = OrderPayment.objects.get(pk=self.payment.order_payment.id)
        self.assertEqual(self.payment.status, 'settled')
        self.assertEqual(order_payment.status, 'settled')
        self.assertEqual(order_payment.order.status, 'success')
