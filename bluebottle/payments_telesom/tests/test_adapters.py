from moneyed.classes import Money, USD
from mock import patch

from django.test.utils import override_settings

from bluebottle.payments_telesom.adapters import TelesomPaymentAdapter
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

telesom_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'telesom',
            'currency': 'USD',
            'api_domain': 'fake://url',
            'merchant_id': '123456',
            'merchant_key': '123456789',
            'username': 'test',
            'password': 'secret'
        }
    ]
}


@override_settings(**telesom_settings)
class TelesomPaymentAdapterTestCase(BluebottleTestCase):

    @patch('bluebottle.payments_telesom.gateway.Client')
    def test_create_success_payment(self, mock_client):
        """
        Test Flutterwave payment that turns to success without otp (one time pin)
        """
        instance = mock_client.return_value
        instance.create.return_value = {'order_key': 123, 'order_id': 123}
        instance.service.PaymentRequest.return_value = "2001! Success, Waiting Confirmation !747"
        instance.service.ProcessPayment.return_value = "4005! This payment is not yet Approved"

        integration_data = {'mobile': '123456789'}
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(70, USD), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='telesomZaad',
                                                   order=order,
                                                   integration_data=integration_data)
        adapter = TelesomPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(int(adapter.payment.amount), 70)
        self.assertEqual(adapter.payment.status, 'started')
        self.assertEqual(adapter.payment.transaction_reference, '747')
        self.assertEqual(authorization_action, {
            "payload": {
                "method": "telesom-sms",
                "text": "Confirm the payment by SMS"
            },
            "type": "step2",
        })

        # Now confirm the payment by user and have gateway send a success
        instance.service.ProcessPayment.return_value = "2001! Your account was Credited with $5.0000 Charge fee $ 0"
        order_payment.integration_data = {}
        adapter = TelesomPaymentAdapter(order_payment)
        adapter.check_payment_status()
        authorization_action = adapter.get_authorization_action()
        self.assertEqual(int(adapter.payment.amount), 70)
        self.assertEqual(adapter.payment.status, 'settled')
        self.assertEqual(authorization_action, {
            "type": "success"
        })
