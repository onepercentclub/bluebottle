from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from mock import patch
from moneyed.classes import Money

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
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
    'data': {
        'status': 'successful'
    }
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
        self.project = ProjectFactory(amount_needed=Money(100000, 'NGN'),
                                      currencies=['USD', 'NGN'],
                                      status=campaign)

    @patch('bluebottle.payments_flutterwave.adapters.FlutterwaveCreditcardPaymentAdapter.post',
           return_value=success_response)
    def test_flutterwave_donation_api(self, mock_post):
        # Create Order with a typical payload
        data = {
            'country': None,
            'created': None,
            'meta_data': None,
            'status': "",
            'total_amount': None,
            'user': None
        }
        response = self.client.post(reverse('order-manage-list'), data,
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
            "project": self.project.slug,
            "reward": None,
            "fundraiser": None,
            "user": None
        }

        response = self.client.post(reverse('manage-donation-list'), data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'created')

        integration_data = {
            'tx_ref': order_id
        }

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
        self.assertEqual(response.data['status'], 'settled')
        self.assertEqual(response.data['payment_method'], 'flutterwaveCreditcard')
        self.assertEqual(response.data['authorization_action']['type'], 'success')
