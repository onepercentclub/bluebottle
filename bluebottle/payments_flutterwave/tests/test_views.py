import json
from urlparse import urlparse

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from moneyed.classes import XOF, Money

from bluebottle.test.utils import BluebottleTestCase

from bluebottle.payments_flutterwave.tests.factory_models import (
    FlutterwaveOrderPaymentFactory, FlutterwavePaymentFactory
)

flutterwave_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'flutterwave',
            'currency': 'NGN',
            'merchant_key': '123456789',
            'api_key': '123456789123456789',
            'api_url': 'http://staging1flutterwave.co:8080/'
        }
    ],
    'PAYMENT_METHODS': [{
        'provider': 'flutterwave',
        'id': 'flutterwave-verve',
        'profile': 'verve',
        'name': 'Verve',
        'currencies': {'NGN': {}},
        'supports_recurring': False,
    }]
}


success_response = {
    "data": {
        "responsecode": "00",
        "responsemessage": "Success",
        "transactionreference": "FLW001"
    },
    "status": "success"
}

failure_response = {
    "data": {
        "responsecode": "7",
        "responsemessage": "This doesn't look right",
    },
    "status": "success"
}

another_failure_response = {
    "data": {
        "responsecode": "RR",
        "responsemessage": "Another this went wrong",
    },
    "status": "success"
}


@patch('bluebottle.payments_flutterwave.adapters.get_current_host',
       return_value='https://onepercentclub.com')
@override_settings(**flutterwave_settings)
class FlutterwaveRedirectTest(BluebottleTestCase):
    def setUp(self):
        super(FlutterwaveRedirectTest, self).setUp()

        self.order_payment = FlutterwaveOrderPaymentFactory.create(amount=Money(2000, XOF))
        self.payment = FlutterwavePaymentFactory.create(order_payment=self.order_payment)
        self.update_url = reverse('flutterwave-payment-response', args=[self.order_payment.id])

    @patch('flutterwave.card.Card.verifyCharge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(success_response)}))
    def test_valid_redirect(self, get_current_host, validate):
        response = self.client.get(self.update_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'settled')
        path = urlparse(response['location']).path

        self.assertEqual(path, '/orders/{}/success'.format(self.order_payment.order.id))

    @patch('flutterwave.card.Card.verifyCharge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(failure_response)}))
    def test_invalid_redirect(self, get_current_host, validate):
        response = self.client.get(self.update_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')
        path = urlparse(response['location']).path

        self.assertEqual(path, '/orders/{}/failed'.format(self.order_payment.order.id))

    @patch('flutterwave.card.Card.verifyCharge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(another_failure_response)}))
    def test_invalid_redirect_another(self, get_current_host, validate):
        response = self.client.get(self.update_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'failed')
        path = urlparse(response['location']).path

        self.assertEqual(path, '/orders/{}/failed'.format(self.order_payment.order.id))
