from mock import patch
from moneyed.classes import Money, XOF

from django.test import SimpleTestCase
from django.test.utils import override_settings

from ..adapters import VitepayPaymentAdapter


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


class Payment(object):
    def __init__(self):
        self.order_id = 'opc-1'
        self.amount_100 = 200000
        self.currency_code = 'XOF'
        self.callback_url = 'http://localhost/'


class OrderPayment(object):
    payment_method = 'vitepayOrangemoney'

    def __init__(self):
        self.amount = Money(2000, XOF)


@patch('bluebottle.payments_vitepay.models.VitepayPayment.objects.get', return_value=None)
@patch('bluebottle.payments_vitepay.adapters.VitepayPaymentAdapter.create_payment')
@override_settings(**vitepay_settings)
class TestAuthenticityHash(SimpleTestCase):
    def test_create_payment_hash(self, create_payment, objects_get):
        create_payment.return_value = Payment()
        order_payment = OrderPayment()
        adapter = VitepayPaymentAdapter(order_payment=order_payment)

        self.assertEqual(adapter._create_payment_hash(),
                         'eebd7734be0470822962c632ec5a2075f46c27cd')

    def test_create_update_hash(self, create_payment, objects_get):
        create_payment.return_value = Payment()
        order_payment = OrderPayment()
        adapter = VitepayPaymentAdapter(order_payment=order_payment)

        self.assertEqual(adapter._create_update_hash(),
                         '64d7effd1c2540f0c9230dbb680c100dd2558d63'.upper())
