from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from moneyed.classes import Money, NGN, EUR
from mock import patch

from bluebottle.payments.models import OrderPayment
from bluebottle.payments_interswitch.adapters import InterswitchPaymentAdapter
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

interswitch_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'interswitch',
            'currency': 'NGN',
            'product_id': '1234',
            'item_id': '123',
            'hashkey': '123456789012345678901234567890123456789012345678901234567890',
            'payment_url': 'https://stageserv.interswitchng.com/test_paydirect/pay',
            'status_url': 'https://stageserv.interswitchng.com/test_paydirect/api/v1/gettransaction.json'
        }
    ]
}


@override_settings(**interswitch_settings)
class InterswitchPaymentAdapterTestCase(BluebottleTestCase):

    @patch('bluebottle.payments_interswitch.adapters.get_current_host', return_value='https://onepercentclub.com')
    def test_create_payment(self, get_current_host):
        self.order_payment = OrderPaymentFactory.create(payment_method='interswitchWebpay',
                                                        amount=Money(2000, NGN))
        self.adapter = InterswitchPaymentAdapter(self.order_payment)
        payment = self.adapter.create_payment()

    @patch('bluebottle.payments_interswitch.adapters.get_current_host', return_value='https://onepercentclub.com')
    def test_create_payment_with_wrong_currency(self, get_current_host):
        with self.assertRaises(ImproperlyConfigured):
            self.order_payment = OrderPaymentFactory.create(payment_method='interswitchWebpay',
                                                            amount=Money(200, EUR))
            self.adapter = InterswitchPaymentAdapter(self.order_payment)
