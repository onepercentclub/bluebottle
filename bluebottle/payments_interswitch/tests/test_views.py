import json

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from moneyed.classes import XOF, Money

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


def mocked_invalid_response(*args, **kwargs):
    response = {
        "Amount": 100,
        "CardNumber": None,
        "MerchantReference": "",
        "PaymentReference": None,
        "RetrievalReferenceNumber": None,
        "LeadBankCbnCode": None,
        "LeadBankName": None,
        "SplitAccounts": [],
        "TransactionDate": "2016-01-01T00:00:00"
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

        redirect_url = "http://testserver/orders/{}/success".format(self.order_payment.order.id)
        self.assertRedirects(response, redirect_url,
                             fetch_redirect_response=False)

    @patch('requests.get', side_effect=mocked_success_response)
    def test_payment_status_update(self, requests_get, get_current_host):
        payment_response_url = reverse('interswitch-payment-response',
                                       kwargs={'order_payment_id': self.order_payment.id})
        self.client.get(payment_response_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, StatusDefinition.SETTLED)
        self.assertEqual(self.payment.status_description, "Approved Successful")
        self.assertEqual(self.payment.status_code, "00")

    @patch('requests.get', side_effect=mocked_failed_response)
    def test_payment_failed_status(self, requests_get, get_current_host):
        payment_response_url = reverse('interswitch-payment-response',
                                       kwargs={'order_payment_id': self.order_payment.id})
        self.client.get(payment_response_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, StatusDefinition.FAILED)
        self.assertEqual(self.payment.status_description, "ESocket transaction error")
        self.assertEqual(self.payment.status_code, "Z25")

    @patch('requests.get', side_effect=mocked_invalid_response)
    def test_payment_invalid_status_response(self, requests_get, get_current_host):
        payment_response_url = reverse('interswitch-payment-response',
                                       kwargs={'order_payment_id': self.order_payment.id})
        self.client.get(payment_response_url)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, StatusDefinition.FAILED)
        self.assertEqual(self.payment.status_description, "")
        self.assertEqual(self.payment.status_code, "")

    def test_order_payment_failed_response(self, get_current_host):
        user = self.order_payment.order.user
        user_token = "JWT {0}".format(user.get_jwt_token())

        # First mock check the payment to update the payment status information
        # TODO: might be easier to call check_payment_status
        with patch('requests.get', side_effect=mocked_failed_response):
            payment_response_url = reverse('interswitch-payment-response',
                                           kwargs={'order_payment_id': self.order_payment.id})
            self.client.get(payment_response_url)
            self.payment.refresh_from_db()

        order_payment_response_url = reverse('manage-order-payment-detail',
                                             kwargs={'pk': self.order_payment.id})
        self.client.get(order_payment_response_url, token=user_token)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status_description, "ESocket transaction error")
        self.assertEqual(self.payment.status_code, "Z25")
