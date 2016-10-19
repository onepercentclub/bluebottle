from django.test.utils import override_settings
from moneyed import Money

from bluebottle.payments.adapters import BasePaymentAdapter
from bluebottle.test.factory_models.payments import OrderPaymentFactory, PaymentFactory
from bluebottle.test.utils import BluebottleTestCase


@override_settings(MERCHANT_ACCOUNTS = [{
    'merchant': 'docdata',
    'merchant_password': 'eur_password',
    'currencies': ['EUR'],
    'merchant_name': 'eur_username'
}, {
    'merchant': 'docdata',
    'merchant_password': 'usd_password',
    'currencies': ['USD'],
    'merchant_name': 'usd_username'
}])
class PaymentAdapterTestCase(BluebottleTestCase):
    def setUp(self):
        self.order_payment = OrderPaymentFactory.create(
            payment_method='docdata',
            amount=Money(200, 'EUR')
        )

        PaymentFactory.create(order_payment=self.order_payment)
        self.adapter = BasePaymentAdapter(self.order_payment)

    def test_credentials(self):
        credentials = self.adapter.credentials

        self.assertTrue('EUR'in credentials['currencies'])

    def test_credentials_usd(self):
        self.order_payment.amount = Money(100, 'USD')
        self.order_payment.save()

        credentials = self.adapter.credentials

        self.assertTrue('USD' in credentials['currencies'])
