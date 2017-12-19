from django.test.utils import override_settings
from moneyed import Money

from bluebottle.payments.adapters import BasePaymentAdapter, has_payment_prodiver
from bluebottle.test.factory_models.payments import OrderPaymentFactory, PaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.utils import BluebottleTestCase


@override_settings(MERCHANT_ACCOUNTS=[{
    'merchant': 'docdata',
    'merchant_password': 'eur_password',
    'currency': 'EUR',
    'merchant_name': 'eur_username'
}, {
    'merchant': 'docdata',
    'merchant_password': 'usd_password',
    'currency': 'USD',
    'merchant_name': 'usd_username'
}])
class PaymentAdapterTestCase(BluebottleTestCase):
    def setUp(self):
        self.order = OrderFactory.create(total=Money(200, 'EUR'))
        self.order_payment = OrderPaymentFactory.create(
            payment_method='docdata',
            order=self.order
        )

        PaymentFactory.create(order_payment=self.order_payment)
        self.adapter = BasePaymentAdapter(self.order_payment)

    def test_credentials(self):
        credentials = self.adapter.credentials

        self.assertEqual('EUR', credentials['currency'])

    def test_credentials_usd(self):
        self.order.total = Money(100, 'USD')
        self.order.save()
        self.order_payment.save()

        credentials = self.adapter.credentials

        self.assertEqual('USD', credentials['currency'])

    def test_has_payment_provider(self):
        self.assertTrue(has_payment_prodiver('docdata'))
        self.assertFalse(has_payment_prodiver('adyen'))
