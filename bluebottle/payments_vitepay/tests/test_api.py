from collections import OrderedDict
from decimal import Decimal

from bluebottle.payments.models import OrderPayment
from mock import patch
from moneyed.classes import Money

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase

vitepay_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'vitepay',
            'currency': 'XOF',
            'api_key': '1234',
            'api_secret': '123456789abcdefg',
            'api_url': 'https://api.vitepay.com/v1/prod/payments'
        }
    ],
    'PAYMENT_METHODS': [{
        'provider': 'vitepay',
        'id': 'vitepay-orangemoney',
        'profile': 'orangemoney',
        'name': 'Orange Money',
        'currencies': {'XOF': {}},
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


@override_settings(**vitepay_settings)
class PaymentVitepayApiTests(BluebottleTestCase):
    """
    Test creating an Vitepay donation through api.
    """

    def setUp(self):
        super(PaymentVitepayApiTests, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        campaign = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory(amount_needed=Money(100000, 'XOF'),
                                      currencies=['USD', 'XOF'],
                                      status=campaign)

    @patch('bluebottle.payments_vitepay.adapters.requests.post',
           return_value=type('obj', (object,),
                             {'status_code': 200, 'content': 'https://vitepay.com/some-path-to-pay'}))
    @patch('bluebottle.payments_vitepay.adapters.VitepayPaymentAdapter._create_payment_hash',
           return_value='123123')
    def test_vitepay_donation_api(self, create_hash, mock_post):
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
            "amount": '{"amount":2500, "currency":"XOF"}',
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

        # Select Vitepay as payment method
        data = {
            "payment_method": "vitepayOrangemoney",
            "integration_data": {"payment_method": "orangemoney"},
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
        order_payment = OrderPayment.objects.get(order_id=order_id)

        expected = {
            'status': u'started',
            'status_description': u'',
            'status_code': u'',
            'payment_method': u'vitepayOrangemoney',
            'order': order_id,
            'amount': {'currency': 'XOF', 'amount': Decimal('2500.00')},
            'authorization_action': OrderedDict([
                ('type', 'redirect'),
                ('method', 'get'),
                ('url', u'https://vitepay.com/some-path-to-pay'),
                ('payload', u''),
                ('data', u'')
            ]),
            'integration_data': {},
            'id': order_payment.id
        }
        self.assertEqual(response.data, expected)
