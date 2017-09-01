import json

from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from moneyed.classes import XOF, Money

from bluebottle.test.utils import BluebottleTestCase

from .factory_models import VitepayOrderPaymentFactory, VitepayPaymentFactory

vitepay_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'vitepay',
            'currency': 'XOF',
            'api_key': '123',
            'api_secret': '123456789012345678901234567890123456789012345678901234567890',
            'payment_url': 'https://api.vitepay.com/v1/prod/payments'
        }
    ]
}


@patch('bluebottle.payments_vitepay.adapters.get_current_host',
       return_value='https://onepercentclub.com')
@override_settings(**vitepay_settings)
class VitepayUpdateApiTest(BluebottleTestCase):
    def setUp(self):
        super(VitepayUpdateApiTest, self).setUp()

        order_payment = VitepayOrderPaymentFactory.create(amount=Money(2000, XOF))
        self.payment = VitepayPaymentFactory.create(order_id='opc-1', order_payment=order_payment)

    def test_valid_update(self, get_current_host):
        data = {
            'success': 1,
            'authenticity': '69E78BC6C64D43DA76DEB90F911AF213DA9DE89D',
            'order_id': 'opc-1'
        }
        response = self.client.post(
            reverse('vitepay-status-update'), data, format='multipart')

        self.payment.refresh_from_db()
        data = json.loads(response.content)
        self.assertEqual(data['status'], '1')
        self.assertEqual(self.payment.status, 'settled')

    def test_invalid_update(self, get_current_host):
        data = {}
        response = self.client.post(
            reverse('vitepay-status-update'), data, format='multipart')

        data = json.loads(response.content)
        self.assertEqual(data['status'], '0')
        self.assertEqual(data['message'], 'Order not found.')

    def test_invalid_auth(self, get_current_host):
        data = {
            'success': 1,
            'authenticity': 'blahblah',
            'order_id': 'opc-1'
        }
        response = self.client.post(
            reverse('vitepay-status-update'), data, format='multipart')

        data = json.loads(response.content)
        self.assertEqual(data['status'], '0')

    def test_mixed_status(self, get_current_host):
        data = {
            'success': 1,
            'failure': 1,
            'authenticity': '69E78BC6C64D43DA76DEB90F911AF213DA9DE89D',
            'order_id': 'opc-1'
        }
        response = self.client.post(
            reverse('vitepay-status-update'), data, format='multipart')

        data = json.loads(response.content)
        self.assertEqual(data['status'], '0')

    def test_no_status(self, get_current_host):
        data = {
            'authenticity': '69E78BC6C64D43DA76DEB90F911AF213DA9DE89D',
            'order_id': 'opc-1'
        }
        response = self.client.post(
            reverse('vitepay-status-update'), data, format='multipart')

        data = json.loads(response.content)
        self.assertEqual(data['status'], '0')

    def test_failed_status(self, get_current_host):
        data = {
            'failure': 1,
            'authenticity': '69E78BC6C64D43DA76DEB90F911AF213DA9DE89D',
            'order_id': 'opc-1'
        }
        response = self.client.post(
            reverse('vitepay-status-update'), data, format='multipart')

        self.payment.refresh_from_db()
        data = json.loads(response.content)
        self.assertEqual(data['status'], '1')
        self.assertEqual(self.payment.status, 'failed')
