import ast

from bluebottle.payments.models import OrderPayment
from mock import patch
from moneyed.classes import Money

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


interswitch_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'interswitch',
            'currency': 'NGN',
            'product_id': '1234',
            'item_id': '123',
            'hashkey': '123456789012345678901234567890123456789012345678901234567890',
            'payment_url': 'https://stageserv.interswitchng.com/test_paydirect/pay',
            'status_url': 'https://stageserv.interswitchng.com/test_paydirect/api/v1/gettransaction.json'
        }
    ],
    'PAYMENT_METHODS': [{
        'provider': 'interswitch',
        'id': 'interswitch-webpay',
        'profile': 'webpay',
        'name': 'WebPay',
        'currencies': {'NGN': {}},
        'supports_recurring': False,
    }, {
        'provider': 'mock',
        'id': 'mock-creditcard',
        'profile': 'creditcard',
        'name': 'MockCard',
        'supports_recurring': False,
        'currencies': {
            'USD': {'min_amount': 5},
        }
    }]
}


@override_settings(**interswitch_settings)
class PaymentInterswitchApiTests(BluebottleTestCase):
    """
    Test creating an Interswitch donation through api.
    """

    def setUp(self):
        super(PaymentInterswitchApiTests, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        campaign = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory(amount_needed=Money(100000, 'NGN'),
                                      currencies=['USD', 'NGN'],
                                      status=campaign)

    @patch('bluebottle.payments_interswitch.adapters.InterswitchPaymentAdapter._create_hash',
           return_value='123123')
    def test_interswitch_donation_api(self, create_hash):
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

        # Select Interswitch as payment method
        data = {
            "payment_method": "interswitchWebpay",
            "integration_data": {"payment_method": "webpay"},
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
        order_payment = OrderPayment.objects.get(order_id=order_id)

        expected = {
            'hash': '123123',
            'txn_ref': '-{0}'.format(order_payment.id),
            'product_id': '1234',
            'site_redirect_url': 'http://testserver/payments_interswitch/payment_response/{0}'.format(order_payment.id),
            'local_date_time': None,
            'cust_name': self.user.full_name,
            'currency': '566',
            'amount': 250000,
            'pay_item_name': None,
            'cust_id': self.user.id,
            'pay_item_id': '123',
            'site_name': 'testserver',
            'cust_id_desc': None,
            'cust_name_desc': None
        }
        self.assertEqual(response.data['payment_method'], 'interswitchWebpay')

        payload = ast.literal_eval(response.data['authorization_action']['payload'])
        self.assertEqual(payload['product_id'], expected['product_id'])
        self.assertEqual(payload['txn_ref'], expected['txn_ref'])
        self.assertEqual(payload['amount'], expected['amount'])
        self.assertEqual(payload['cust_name'], expected['cust_name'])
        self.assertEqual(payload['site_redirect_url'], expected['site_redirect_url'])
        self.assertEqual(payload['site_name'], expected['site_name'])
