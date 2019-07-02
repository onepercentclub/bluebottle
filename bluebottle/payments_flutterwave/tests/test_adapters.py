from django.test.utils import override_settings
from mock import patch
from moneyed.classes import Money, NGN

from bluebottle.payments.exception import PaymentException
from bluebottle.payments_flutterwave.adapters import FlutterwaveCreditcardPaymentAdapter
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

flutterwave_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'flutterwave',
            'currency': 'NGN',
            'sec_key': '123456789123456789',
            'pub_key': '123456789123456789'
        }
    ]
}

success_response = {
    'status': 'success',
    'data': {}
}


failed_response = {
    'status': 'failed',
    'data': {}
}


@override_settings(**flutterwave_settings)
class FlutterwavePaymentAdapterTestCase(BluebottleTestCase):

    @patch('bluebottle.payments_flutterwave.adapters.FlutterwaveCreditcardPaymentAdapter.post',
           return_value=success_response)
    def test_create_success_payment(self, mock_post):
        """
        Test Flutterwave payment that turns to success without otp (one time pin)
        """
        self.init_projects()
        order = OrderFactory.create()
        integration_data = {
            'tx_ref': order.id
        }
        DonationFactory.create(amount=Money(150000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   integration_data=integration_data)
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(adapter.payment.amount, '150000.00')
        self.assertEqual(adapter.payment.status, 'settled')
        self.assertEqual(adapter.payment.transaction_reference, order.id)
        self.assertEqual(authorization_action, {
            "type": "success"
        })

    @patch('bluebottle.payments_flutterwave.adapters.FlutterwaveCreditcardPaymentAdapter.post',
           return_value=success_response)
    def test_create_payment_incomplete(self, mock_post):
        """
        Test Flutterwave payment throws an error when incomplete data is sent
        """
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(150000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   integration_data={})
        with self.assertRaises(PaymentException):
            FlutterwaveCreditcardPaymentAdapter(order_payment)

    @patch('bluebottle.payments_flutterwave.adapters.FlutterwaveCreditcardPaymentAdapter.post',
           return_value=failed_response)
    def test_create_payment_flutter_fail(self, mock_post):
        """
        Make sure we catch errors from Flutterwave
        """
        self.init_projects()
        order = OrderFactory.create()
        integration_data = {
            'tx_ref': order.id
        }
        DonationFactory.create(amount=Money(150000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   integration_data=integration_data)
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        with self.assertRaises(PaymentException):
            adapter.get_authorization_action()
