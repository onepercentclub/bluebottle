import json

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from moneyed.classes import EUR, XOF, Money

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition

from .factory_models import InterswitchOrderPaymentFactory, InterswitchPaymentFactory

interswitch_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'interswitch',
            'currency': 'XOF',
            'api_key': '123',
            'api_secret': '123456789012345678901234567890123456789012345678901234567890',
            'payment_url': 'https://stageserv.interswitchng.com/test_paydirect/pay',
            'status_url': 'https://stageserv.interswitchng.com/test_paydirect/api/v1/gettransaction.json',
            'hashkey': 'blahblah'
        }
    ]
}




class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data 
        self.content = json.dumps(json_data) 
        self.status_code = status_code

    def json(self):
        return self.json_data


def mocked_success_response(*args, **kwargs):
    response = {
        "Amount": 100,
        "CardNumber": None,
        "MerchantReference": "",
        "PaymentReference": None,
        "RetrievalReferenceNumber": None,
        "LeadBankCbnCode": None,
        "LeadBankName": None,
        "SplitAccounts": [],
        "TransactionDate": "2016-01-01T00:00:00",
        "ResponseCode": "00",
        "ResponseDescription": "Approved Successful"
    }

    return MockResponse(response, 200)


def mocked_failed_response(*args, **kwargs):
    response = {
        "Amount": 100,
        "CardNumber": None,
        "MerchantReference": "",
        "PaymentReference": None,
        "RetrievalReferenceNumber": None,
        "LeadBankCbnCode": None,
        "LeadBankName": None,
        "SplitAccounts": [],
        "TransactionDate": "2016-01-01T00:00:00",
        "ResponseCode": "Z25",
        "ResponseDescription": "ESocket transaction error"
    }

    return MockResponse(response, 200)


@patch('bluebottle.payments_interswitch.adapters.get_current_host',
        return_value='https://onepercentclub.com')
@override_settings(**interswitch_settings) 
class InterswitchUpdateApiTest(BluebottleTestCase):
    def setUp(self):
        super(InterswitchUpdateApiTest, self).setUp()

        self.order_payment = InterswitchOrderPaymentFactory.create(amount=Money(2000, XOF))
        self.payment = InterswitchPaymentFactory.create(order_payment=self.order_payment)

    @patch('requests.get', side_effect=mocked_success_response)
    def test_get_payment(self, requests_get, get_current_host):
        payment_response_url = reverse('interswitch-payment-response',
                        kwargs={'order_payment_id': self.order_payment.id})
        response = self.client.get(payment_response_url)

        # import ipdb; ipdb.set_trace()
        redirect_url = "http://testserver/orders/{}/success".format(self.order_payment.order.id)
        self.assertRedirects(response, redirect_url,
                             fetch_redirect_response=False) 

    @patch('requests.get', side_effect=mocked_success_response)
    def test_payment_status_update(self, requests_get, get_current_host):
        payment_response_url = reverse('interswitch-payment-response',
                        kwargs={'order_payment_id': self.order_payment.id})
        response = self.client.get(payment_response_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, StatusDefinition.SETTLED)

    @patch('requests.get', side_effect=mocked_failed_response)
    def test_payment_failed_status(self, requests_get, get_current_host):
        payment_response_url = reverse('interswitch-payment-response',
                        kwargs={'order_payment_id': self.order_payment.id})
        response = self.client.get(payment_response_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, StatusDefinition.FAILED)
