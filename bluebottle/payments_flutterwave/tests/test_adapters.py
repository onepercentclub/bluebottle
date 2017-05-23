import json

from bluebottle.payments.exception import PaymentException
from moneyed.classes import Money, NGN
from mock import patch

from django.test.utils import override_settings

from bluebottle.payments_flutterwave.adapters import FlutterwaveCreditcardPaymentAdapter
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.utils import BluebottleTestCase

flutterwave_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'flutterwave',
            'currency': 'NGN',
            'merchant_key': '123456789',
            'api_key': '123456789123456789',
            'payment_url': 'http://staging1flutterwave.co:8080/pwc/rest/card/mvva/pay',
            'status_url': 'http://staging1flutterwave.co:8080/pwc/rest/card/mvva/status'
        }
    ]
}

success_response = {
    "data": {
        "responsecode": "00",
        "responsemessage": "Success",
        "transactionreference": "FLW001"
    },
    "status": "success"
}

otp_required_response = {
    "data": {
        "responsecode": "02",
        "responsemessage": "Kindly enter the OTP sent to 234803***9051 and henry***********ture.com.",
        "transactionreference": "FLW004"
    },
    "status": "success"
}

redirect_response = {
    "data": {
        "responsecode": "02",
        "authurl": "https://prod1flutterwave.co:8181/pwc/xfaO8bIrrXUKpuU.html",
        "responsemessage": "Pending Validation",
        "transactionreference": "FLW005"
    },
    "status": "success"
}

failure_response = {
    "data": {
        "responsecode": "7",
        "responsemessage": "This doesn't look right",
    },
    "status": "success"
}

integration_data = {
    "auth_model": "PIN",
    "card_number": "123456789",
    "expiry_month": "01",
    "expiry_year": "25",
    "cvv": "123",
    "pin": "1111"
}


@override_settings(**flutterwave_settings)
class FlutterwavePaymentAdapterTestCase(BluebottleTestCase):
    @patch('flutterwave.card.Card.charge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(success_response)}))
    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_create_success_payment(self, charge, get_current_host):
        """
        Test Flutterwave payment that turns to success without otp (one time pin)
        """
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(150000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   integration_data=integration_data)
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(adapter.payment.amount, '150000.00')
        self.assertEqual(adapter.payment.status, 'authorized')
        self.assertEqual(adapter.payment.transaction_reference, 'FLW001')
        self.assertEqual(authorization_action, {
            "type": "success"
        })

    @patch('flutterwave.card.Card.charge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(redirect_response)}))
    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_create_payment_redirect(self, charge, get_current_host):
        """
        Test Flutterwave payment that turns to success without otp (one time pin)
        """
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(150000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   integration_data=integration_data)
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(adapter.payment.amount, '150000.00')
        self.assertEqual(adapter.payment.status, 'started')
        self.assertEqual(adapter.payment.transaction_reference, 'FLW005')
        self.assertEqual(authorization_action, {
            'method': 'get',
            'payload': {
                'method': 'flutterwave-otp',
                'text': redirect_response['data']['responsemessage']
            },
            'type': 'redirect',
            'url': redirect_response['data']['authurl']
        })

    @patch('flutterwave.card.Card.charge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(otp_required_response)}))
    @patch('flutterwave.card.Card.validate',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(success_response)}))
    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_create_otp_payment(self, charge, validate, get_current_host):
        """
        Test Flutterwave payment that needs a otp (one time pin)
        """
        self.init_projects()
        order = OrderFactory.create()
        user = BlueBottleUserFactory(first_name=u'T\xc3\xabst user')
        DonationFactory.create(amount=Money(20000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   user=user,
                                                   integration_data=integration_data)
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(adapter.payment.amount, '20000.00')
        self.assertEqual(adapter.payment.status, 'started')
        self.assertEqual(adapter.payment.transaction_reference, 'FLW004')
        self.assertEqual(authorization_action, {
            "type": "step2",
            "payload": {
                "method": "flutterwave-otp",
                "text": "Kindly enter the OTP sent to 234803***9051 and henry***********ture.com."
            }
        })

        # Now set the otp
        order_payment.integration_data = {'otp': '123456'}
        order_payment.save()
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        adapter.check_payment_status()
        self.assertEqual(adapter.payment.status, 'settled')

    @patch('flutterwave.card.Card.charge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(otp_required_response)}))
    @patch('flutterwave.card.Card.validate',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(failure_response)}))
    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_create_otp_payment_failure(self, charge, validate, get_current_host):
        """
        Test Flutterwave payment that needs a otp (one time pin)
        """
        self.init_projects()
        order = OrderFactory.create()
        user = BlueBottleUserFactory(first_name=u'T\xc3\xabst user')
        DonationFactory.create(amount=Money(20000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   user=user,
                                                   integration_data=integration_data)
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        authorization_action = adapter.get_authorization_action()

        self.assertEqual(adapter.payment.amount, '20000.00')
        self.assertEqual(adapter.payment.status, 'started')
        self.assertEqual(adapter.payment.transaction_reference, 'FLW004')
        self.assertEqual(authorization_action, {
            "type": "step2",
            "payload": {
                "method": "flutterwave-otp",
                "text": "Kindly enter the OTP sent to 234803***9051 and henry***********ture.com."
            }
        })

        # Now set the otp
        order_payment.integration_data = {'otp': '123456'}
        order_payment.save()
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        with self.assertRaises(PaymentException):
            adapter.check_payment_status()
            self.assertEqual(adapter.payment.status, 'failed')

    @patch('flutterwave.card.Card.charge',
           return_value=type('obj', (object,), {'status_code': 500,
                                                'text': 'This is crazy business man'}))
    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_create_payment_incomplete(self, charge, get_current_host):
        """
        Test Flutterwave payment throws an error when incomplete data is sent
        """
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(150000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   integration_data={'card_number': '123blabla'})
        with self.assertRaises(PaymentException):
            FlutterwaveCreditcardPaymentAdapter(order_payment)

    @patch('flutterwave.card.Card.charge',
           return_value=type('obj', (object,), {'status_code': 500,
                                                'text': 'This is crazy business man'}))
    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_create_payment_flutter_fail(self, charge, get_current_host):
        """
        Make sure we catch errors from Flutterwave
        """
        self.init_projects()
        order = OrderFactory.create()
        DonationFactory.create(amount=Money(150000, NGN), order=order)
        order_payment = OrderPaymentFactory.create(payment_method='flutterwaveCreditcard',
                                                   order=order,
                                                   integration_data=integration_data)
        adapter = FlutterwaveCreditcardPaymentAdapter(order_payment)
        with self.assertRaises(PaymentException):
            adapter.get_authorization_action()
