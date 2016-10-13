from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings

from moneyed.classes import Money, XOF, EUR
from mock import patch

from bluebottle.payments_vitepay.adapters import VitepayPaymentAdapter
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

vitepay_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'vitepay',
            'currency': 'XOF',
            'item_id': '123',
            'api_secret': '123456789012345678901234567890123456789012345678901234567890',
            'payment_url': 'https://api.vitepay.com/v1/prod/payments'
        }
    ]
}


@override_settings(**vitepay_settings)
class VitepayPaymentAdapterTestCase(BluebottleTestCase):

    @patch('bluebottle.payments_vitepay.adapters.get_current_host', return_value='https://onepercentclub.com')
    def test_create_payment(self, get_current_host):
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(2000, XOF), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='vitepayOrangeMoney', order=order)
        adapter = VitepayPaymentAdapterTestCase(order_payment)
        self.assertEqual(adapter.payment.amount, 200000)

        #  Check generated payload
        payload = adapter._get_payload()
        self.assertEqual(payload['product_id'], '1234')
        self.assertEqual(payload['amount'], 200000)
        self.assertEqual(payload['txn_ref'], 'opc-{0}'.format(order_payment.id))

    @patch('bluebottle.payments_vitepay.adapters.get_current_host',
           return_value='https://onepercentclub.com')
    def test_create_payment_with_wrong_currency(self, get_current_host):
        with self.assertRaises(ImproperlyConfigured):
            order_payment = OrderPaymentFactory.create(payment_method='vitepayOrangeMoney',
                                                       amount=Money(200, EUR))
            VitepayPaymentAdapterTestCase(order_payment)

    @patch('bluebottle.payments_vitepay.adapters.get_current_host',
           return_value='https://onepercentclub.com')
    def test_create_payment_with_wrong_payment_method(self, get_current_host):
        with self.assertRaises(ImproperlyConfigured):
            order_payment = OrderPaymentFactory.create(payment_method='docdataIdeal',
                                                       amount=Money(3500, XOF))
            VitepayPaymentAdapterTestCase(order_payment)
