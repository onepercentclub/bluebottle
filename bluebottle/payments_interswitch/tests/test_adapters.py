from moneyed.classes import Money, NGN, EUR
from mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings

from bluebottle.payments_interswitch.adapters import InterswitchPaymentAdapter
from bluebottle.payments_interswitch.models import InterswitchPayment
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

interswitch_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'interswitch',
            'currencies': ['NGN'],
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
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(2000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='interswitchWebpay', order=order)
        adapter = InterswitchPaymentAdapter(order_payment)
        self.assertEqual(adapter.payment.amount, 200000)

        #  Check generated payload
        payload = adapter._get_payload()
        self.assertEqual(payload['product_id'], '1234')
        self.assertEqual(payload['amount'], 200000)
        self.assertEqual(payload['txn_ref'], 'opc-{0}'.format(order_payment.id))

    @patch('bluebottle.payments_interswitch.adapters.get_current_host', return_value='https://onepercentclub.com')
    def test_create_only_one_payment(self, get_current_host):
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(2000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='interswitchWebpay', order=order)
        InterswitchPaymentAdapter(order_payment)
        self.assertEqual(InterswitchPayment.objects.count(), 1)
        InterswitchPaymentAdapter(order_payment)
        self.assertEqual(InterswitchPayment.objects.count(), 1)

    @patch('bluebottle.payments_interswitch.adapters.get_current_host',
           return_value='https://onepercentclub.com')
    def test_create_payment_with_wrong_currency(self, get_current_host):
        with self.assertRaises(ImproperlyConfigured):
            order_payment = OrderPaymentFactory.create(payment_method='interswitchWebpay',
                                                       amount=Money(200, EUR))
            InterswitchPaymentAdapter(order_payment)

    @patch('bluebottle.payments_interswitch.adapters.get_current_host',
           return_value='https://onepercentclub.com')
    def test_create_payment_with_wrong_payment_method(self, get_current_host):
        with self.assertRaises(ImproperlyConfigured):
            order_payment = OrderPaymentFactory.create(payment_method='docdataIdeal',
                                                       amount=Money(3500, NGN))
            InterswitchPaymentAdapter(order_payment)
