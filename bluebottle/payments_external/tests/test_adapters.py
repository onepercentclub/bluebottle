from moneyed.classes import Money, EUR

from django.test.utils import override_settings

from ..adapters import ExternalPaymentAdapter
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

external_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'external',
            'currency': 'EUR'
        }
    ],
    'PAYMENT_METHODS': [
        {
            'provider': 'docdata',
            'id': 'external-money',
            'profile': 'cash',
            'name': 'Externa;',
            'supports_recurring': False,
            'currencies': {
                'EUR': {
                    'min_amount': 1
                }
            }
        }
    ],
    'PAYOUT_METHODS': [
        {
            'method': 'external',
            'payment_methods': [
                'docdata-directdebit',
                'docdata-creditcard',
                'docdata-ideal'
            ],
            'currencies': ['EUR'],
            'account_name': "Donatierekening",
            'account_bic': "RABONL2U",
            'account_iban': "NL45RABO0132207044"
        }
    ],
}


@override_settings(**external_settings)
class ExternalPaymentAdapterTestCase(BluebottleTestCase):

    def test_create_success_payment(self):
        """
        Test External payment
        """
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(70, EUR), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='externalMoney', order=order)
        order_payment.started()
        adapter = ExternalPaymentAdapter(order_payment)
        adapter.check_payment_status()
        self.assertEqual(adapter.payment.status, 'settled')
