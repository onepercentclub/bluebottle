import json

from bluebottle.test.factory_models.orders import OrderFactory
from mock import patch
from moneyed.classes import Money

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


flutterwave_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'flutterwave',
            'currency': 'NGN',
            'merchant_key': '123456789',
            'api_key': '123456789123456789',
            'api_url': 'http://staging1flutterwave.co:8080/'
        },
        {
            'merchant': 'flutterwave',
            'currency': 'KES',
            'business_number': '123545',
            'merchant_key': '123456789',
            'mpesa_base_url': 'http://mpe.sa',
            'api_key': '123456789123456789',
            'api_url': 'http://staging1flutterwave.co:8080/'
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

integration_data = {
    "auth_model": "PIN",
    "card_number": "123456789",
    "expiry_month": "01",
    "expiry_year": "25",
    "cvv": "123",
    "pin": "1111"
}

mpesa_response = {
    "status": "okidoki",
    "description": "This is a mock response, we do not know what Fw will send us."
}


@override_settings(**flutterwave_settings)
class PaymentFlutterwaveApiTests(BluebottleTestCase):
    """
    Test creating an Interswitch donation through api.
    """

    def setUp(self):
        super(PaymentFlutterwaveApiTests, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        campaign = ProjectPhase.objects.get(slug='campaign')
        self.project_ngn = ProjectFactory(amount_needed=Money(100000, 'NGN'),
                                          currencies=['USD', 'NGN'],
                                          status=campaign)
        self.project_kes = ProjectFactory(amount_needed=Money(100000, 'KES'),
                                          currencies=['USD', 'KES'],
                                          status=campaign)

    @patch('flutterwave.card.Card.charge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(success_response)}))
    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_flutterwave_donation_api(self, current_host, charge):
        # Create Order with a typical payload
        data = {
            'country': None,
            'created': None,
            'meta_data': None,
            'status': "",
            'total_amount': None,
            'user': None
        }
        response = self.client.post(reverse('manage-order-list'), data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'created')
        order_id = response.data['id']

        # Create a donation
        data = {
            "completed": None,
            "amount": '{"amount":2500, "currency":"NGN"}',
            "created": None,
            "anonymous": False,
            "meta_data": None,
            "order": order_id,
            "project": self.project_ngn.slug,
            "reward": None,
            "fundraiser": None,
            "user": None
        }

        response = self.client.post(reverse('manage-donation-list'), data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'created')

        # Select Flutterwave as payment method
        data = {
            "payment_method": "flutterwaveCreditcard",
            "integration_data": integration_data,
            "authorization_action": None,
            "status": "",
            "created": None,
            "updated": None,
            "closed": None,
            "amount": None,
            "meta_data": None,
            "user": None,
            "order": order_id
        }
        response = self.client.post(reverse('manage-order-payment-list'), data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'authorized')
        self.assertEqual(response.data['payment_method'], 'flutterwaveCreditcard')
        self.assertEqual(response.data['authorization_action']['type'], 'success')

    @patch('flutterwave.card.Card.charge',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(otp_required_response)}))
    @patch('flutterwave.card.Card.validate',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(success_response)}))
    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_flutterwave_otp_donation_api(self, get_current_host, charge, validate):
        """
        Make a donation with Flutterwave that needs otp
        """

        # Create Order with a typical payload
        data = {
            'country': None,
            'created': None,
            'meta_data': None,
            'status': "",
            'total_amount': None,
            'user': None
        }
        response = self.client.post(reverse('manage-order-list'), data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'created')
        order_id = response.data['id']

        # Create a donation
        data = {
            "completed": None,
            "amount": '{"amount":2500, "currency":"NGN"}',
            "created": None,
            "anonymous": False,
            "meta_data": None,
            "order": order_id,
            "project": self.project_ngn.slug,
            "reward": None,
            "fundraiser": None,
            "user": None
        }

        response = self.client.post(reverse('manage-donation-list'), data, token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'created')

        # Select Flutterwave as payment method
        data = {
            "payment_method": "flutterwaveCreditcard",
            "integration_data": integration_data,
            "authorization_action": None,
            "status": "",
            "created": None,
            "updated": None,
            "closed": None,
            "amount": None,
            "meta_data": None,
            "user": None,
            "order": order_id
        }
        response = self.client.post(reverse('manage-order-payment-list'), data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'started')
        order_payment_url = reverse('manage-order-payment-detail', kwargs={'pk': response.data['id']})
        self.assertEqual(response.data['payment_method'], 'flutterwaveCreditcard')
        self.assertEqual(response.data['authorization_action']['type'], 'step2')

        # Now let's update it with an OTP
        data['integration_data'] = {"otp": "123456"}
        response2 = self.client.put(order_payment_url, data, token=self.user_token)
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.data['authorization_action']['type'], 'success')

    @patch('bluebottle.payments_flutterwave.adapters.get_current_host',
           return_value='https://bluebottle.ocean')
    def test_flutterwave_mpesa_donation_api(self, get_current_host):
        # Create Order with a typical payload
        data = {
            'country': None,
            'created': None,
            'meta_data': None,
            'status': "",
            'total_amount': None,
            'user': None
        }
        response = self.client.post(reverse('manage-order-list'), data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'created')
        order_id = response.data['id']

        # Create a donation
        data = {
            "completed": None,
            "amount": '{"amount":2500, "currency":"KES"}',
            "created": None,
            "anonymous": False,
            "meta_data": None,
            "order": order_id,
            "project": self.project_kes.slug,
            "reward": None,
            "fundraiser": None,
            "user": None
        }

        response = self.client.post(reverse('manage-donation-list'), data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'created')

        # Select Flutterwave as payment method
        data = {
            "payment_method": "flutterwaveMpesa",
            "integration_data": integration_data,
            "authorization_action": None,
            "status": "",
            "created": None,
            "updated": None,
            "closed": None,
            "amount": None,
            "meta_data": None,
            "user": None,
            "order": order_id
        }
        response = self.client.post(reverse('manage-order-payment-list'), data,
                                    token=self.user_token)

        # Response should return payment details and type 'process'
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'started')
        self.assertEqual(response.data['payment_method'], 'flutterwaveMpesa')
        self.assertEqual(response.data['authorization_action']['type'], 'process')

        order_payment_id = response.data['id']
        expected_data = {
            'amount': 2500,
            'account_number': order_payment_id,
            'business_number': '123545'
        }
        self.assertEqual(response.data['authorization_action']['data'], expected_data)

    @patch('bluebottle.payments_flutterwave.adapters.requests.get',
           return_value=type('obj', (object,), {'status_code': 200,
                                                'text': json.dumps(mpesa_response)}))
    def test_flutterwave_mpesa_donation_success_api(self, mock_get):
        # Create Order to verify and fake a success response from Fluttewave
        order = OrderFactory(total=Money(1000, 'KES'), user=self.user)
        order_payment = OrderPaymentFactory(order=order)

        order_payment_url = reverse('manage-order-payment-detail', kwargs={'pk': order_payment.id})

        mpesa_data = {
            "amount": 500,
            "account_number": "65685",
            "business_number": "894857"
        }

        # Select Flutterwave as payment method
        data = {
            "payment_method": "flutterwaveMpesa",
            "integration_data": mpesa_data,
            "authorization_action": None,
            "status": "",
            "created": None,
            "updated": None,
            "closed": None,
            "amount": None,
            "meta_data": None,
            "user": None,
            "order": order.id
        }

        response = self.client.put(order_payment_url, data, token=self.user_token)

        # Response should return payment details and type 'success'
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'settled')
        self.assertEqual(response.data['payment_method'], 'flutterwaveMpesa')
        self.assertEqual(response.data['authorization_action']['type'], 'success')

    @patch('bluebottle.payments_flutterwave.adapters.requests.get',
           return_value=type('obj', (object,), {'status_code': 400,
                                                'text': json.dumps(mpesa_response)}))
    def test_flutterwave_mpesa_donation_fail_api(self, mock_get):
        # Create Order to verify and fake a fail response from Fluttewave
        order = OrderFactory(total=Money(1000, 'KES'), user=self.user)
        order_payment = OrderPaymentFactory(order=order)

        order_payment_url = reverse('manage-order-payment-detail', kwargs={'pk': order_payment.id})

        mpesa_data = {
            "amount": 500,
            "account_number": "65685",
            "business_number": "894857"
        }

        # Select Flutterwave as payment method
        data = {
            "payment_method": "flutterwaveMpesa",
            "integration_data": mpesa_data,
            "authorization_action": None,
            "status": "",
            "created": None,
            "updated": None,
            "closed": None,
            "amount": None,
            "meta_data": None,
            "user": None,
            "order": order.id
        }

        response = self.client.put(order_payment_url, data, token=self.user_token)

        # Response should return payment error
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'detail': 'Payment could not be verified yet.'})
