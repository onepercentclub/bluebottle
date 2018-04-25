from moneyed.classes import Money, UGX
from mock import patch

from django.test.utils import override_settings

from bluebottle.payments_beyonic.adapters import BeyonicPaymentAdapter
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

beyonic_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'beyonic',
            'currency': 'UGX',
            'merchant_id': '123456',
            'merchant_key': '123456789',
            'live': True
        }
    ]
}


@override_settings(**beyonic_settings)
class BeyonicPaymentAdapterTestCase(BluebottleTestCase):

    @patch('bluebottle.payments_beyonic.adapters.get_current_host',
           return_value='https://onepercentclub.com')
    @patch('beyonic.CollectionRequest.create')
    @patch('beyonic.CollectionRequest.get')
    def test_create_success_payment(self, mock_get, mock_create, get_current_host):
        """
        Test Flutterwave payment that turns to success without otp (one time pin)
        """
        mock_create.return_value = {'status': 'pending', 'id': 123}
        mock_get.return_value = {'status': 'pending', 'id': 123}

        integration_data = {'mobile': '123456789'}
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(70, UGX), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='beyonicAirtel',
                                                   order=order,
                                                   integration_data=integration_data)
        adapter = BeyonicPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(int(adapter.payment.amount), 70)
        self.assertEqual(adapter.payment.status, 'started')
        self.assertEqual(adapter.payment.transaction_reference, 123)
        self.assertEqual(authorization_action, {
            "payload": {
                "method": "beyonic-sms",
                "text": "Confirm the payment on your mobile"
            },
            "type": "step2",
        })

        # Now confirm the payment by user and have gateway send a success
        mock_get.return_value = {'status': 'successful', 'id': 123}

        order_payment.integration_data = {}
        adapter = BeyonicPaymentAdapter(order_payment)
        adapter.check_payment_status()
        authorization_action = adapter.get_authorization_action()
        self.assertEqual(int(adapter.payment.amount), 70)
        self.assertEqual(adapter.payment.status, 'settled')
        self.assertEqual(authorization_action, {
            "type": "success"
        })
