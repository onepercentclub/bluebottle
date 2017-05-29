from bluebottle.payments.exception import PaymentException
from moneyed.classes import Money, KES
from mock import patch

from django.test.utils import override_settings

from bluebottle.payments_lipisha.adapters import LipishaPaymentAdapter
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

lipisha_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'lipisha',
            'currency': 'KES',
            'api_key': '1234567890',
            'api_signature': '9784904749074987dlndflnlfgnh',
            'business_number': '1234',
            'account_number': '012'
        }
    ]
}

lipisha_success_response = {
    u'content': [
        {
            u'transaction': u'A35EE9256',
            u'transaction_account_name': u'Donations',
            u'transaction_account_number': u'03858',
            u'transaction_amount': u'1500.0000',
            u'transaction_currency': u'KES',
            u'transaction_date': u'2017-05-19 00:15:02',
            u'transaction_email': u'',
            u'transaction_method': u'Paybill (M-Pesa)',
            u'transaction_mobile_number': u'31715283569',
            u'transaction_name': u'ROSE ONESMUS RACHEL',
            u'transaction_reference': u'4312',
            u'transaction_reversal_status': u'None',
            u'transaction_reversal_status_id': u'1',
            u'transaction_status': u'Completed',
            u'transaction_type': u'Payment'
        }
    ],
    u'status': {
        u'status': u'SUCCESS',
        u'status_code': 0,
        u'status_description': u'Transactions Found'
    }
}

lipisha_not_found_response = {
    u'content': [],
    u'status': {
        u'status': u'SUCCESS',
        u'status_code': 4000,
        u'status_description': u'Transactions Not Found'
    }
}


@override_settings(**lipisha_settings)
class LipishaPaymentAdapterTestCase(BluebottleTestCase):

    @patch('bluebottle.payments_lipisha.adapters.Lipisha')
    def test_create_success_payment(self, mock_client):
        """
        Test Lipisha M-PESA payment that turns to success.
        """

        order = OrderFactory.create()
        DonationFactory.create(amount=Money(1500, KES), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='lipishaMpesa',
                                                   order=order)
        adapter = LipishaPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(int(adapter.payment.reference), order_payment.id)

        self.assertEqual(authorization_action, {
            'payload': {
                'account_number': '012#{}'.format(order_payment.id),
                'amount': 1500,
                'business_number': '1234'
            },
            'type': 'process'
        })

        # Now confirm the payment by user and have Lipisha send a success
        instance = mock_client.return_value
        instance.get_transactions.return_value = lipisha_success_response

        order_payment.integration_data = {}
        adapter = LipishaPaymentAdapter(order_payment)
        adapter.check_payment_status()
        authorization_action = adapter.get_authorization_action()
        self.assertEqual(adapter.payment.transaction_amount, '1500.0000')
        self.assertEqual(adapter.payment.status, 'settled')
        self.assertEqual(authorization_action, {
            "type": "success"
        })

    @patch('bluebottle.payments_lipisha.adapters.Lipisha')
    def test_create_failed_payment(self, mock_client):
        """
        Test Lipisha M-PESA payment that turns to success.
        """

        order = OrderFactory.create()
        DonationFactory.create(amount=Money(1500, KES), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='lipishaMpesa',
                                                   order=order)
        adapter = LipishaPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(int(adapter.payment.reference), order_payment.id)

        self.assertEqual(authorization_action, {
            'payload': {
                'account_number': '012#{}'.format(order_payment.id),
                'amount': 1500,
                'business_number': '1234'
            },
            'type': 'process'
        })

        # Now confirm the payment by user and have Lipisha send a not-found
        # we should receive an exception
        instance = mock_client.return_value
        instance.get_transactions.return_value = lipisha_not_found_response

        order_payment.integration_data = {}
        adapter = LipishaPaymentAdapter(order_payment)

        with self.assertRaises(PaymentException):
            adapter.check_payment_status()
