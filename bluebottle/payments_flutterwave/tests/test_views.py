import json
from urlparse import urlparse

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from moneyed.classes import XOF, Money, KES

from bluebottle.test.utils import BluebottleTestCase

from bluebottle.payments_flutterwave.tests.factory_models import (
    FlutterwaveOrderPaymentFactory, FlutterwavePaymentFactory,
    FlutterwaveMpesaPaymentFactory,
    FlutterwaveMpesaOrderPaymentFactory)

flutterwave_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'flutterwave',
            'currency': 'NGN',
            'merchant_key': '123456789',
            'api_key': '123456789123456789',
            'mpesa_base_url': 'https://flutterwavestaging.com:9443/'
        },
        {
            'merchant': 'flutterwave',
            'currency': 'KES',
            'business_number': '123545',
            'merchant_key': '123456789',
            'api_key': '123456789123456789',
            'mpesa_base_url': 'https://flutterwavestaging.com:9443/'
        }
    ]
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


mpesa_update_request = {
    "billrefnumber": "GHA094692",
    "kycinfo": "[Personal Details][First Name]|MWIKALI,[Personal Details]"
               "[Middle Name]|MATU,[Personal Details][Last Name]|MATU,",
    "id": "af758aaa-8fec-c280-8867-08d44c5d66e1",
    "transactionamount": 13141,
    "msisdn": "254722705727",
    "thirdpartytransactionid": "",
    "transactiontime": "20170203205214",
    "transactionid": "LB34YRSLD6",
    "invoicenumber": ""
}

mpesa_response = {
    "status": "okidoki",
    "description": "This is a mock response, we do not know what Fw will send us."
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


@override_settings(**flutterwave_settings)
class FlutterwaveMpesaUpdateTest(BluebottleTestCase):
    def setUp(self):
        super(FlutterwaveMpesaUpdateTest, self).setUp()

        self.order_payment = FlutterwaveMpesaOrderPaymentFactory.create(amount=Money(2000, KES))
        self.payment = FlutterwaveMpesaPaymentFactory.create(order_payment=self.order_payment)
        self.mpesa_update_url = reverse('flutterwave-mpesa-payment-update')

    @patch('bluebottle.payments_flutterwave.adapters.requests.get',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(mpesa_response)}))
    def test_valid_redirect(self, get):
        mpesa_update_request['billrefnumber'] = self.order_payment.id
        self.client.post(self.mpesa_update_url, mpesa_update_request)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'settled')
