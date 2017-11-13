from moneyed.classes import Money

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.payments.models import OrderPayment
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.utils import BluebottleTestCase


lipisha_settings = {
    'MERCHANT_ACCOUNTS': [
        {
            'merchant': 'lipisha',
            'currency': 'KES',
            'api_key': '1234567890',
            'api_signature': '9784904749074987dlndflnlfgnh',
            'business_number': '1234',
            'account_number': '353535'
        }
    ],
    'PAYMENT_METHODS': [{
        'provider': 'lipisha',
        'id': 'lipisha-mpesa',
        'profile': 'mpesa',
        'name': 'M-PESA',
        'currencies': {'KES': {}},
        'supports_recurring': False,
    }]
}


@override_settings(**lipisha_settings)
class PaymentLipishaApiTests(BluebottleTestCase):
    """
    Test creating an Lipisha donation through api.
    """

    def setUp(self):
        super(PaymentLipishaApiTests, self).setUp()
        self.init_projects()
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        campaign = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory(amount_needed=Money(100000, 'KES'),
                                      currencies=['EUR', 'KES'],
                                      status=campaign)

    def test_lipisha_donation_api(self):
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
            "amount": '{"amount":250000, "currency":"KES"}',
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
            "payment_method": "lipishaMpesa",
            "integration_data": {},
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

        self.assertEqual(response.data['payment_method'], 'lipishaMpesa')
        self.assertEqual(response.data['id'], order_payment.id)

        payload = response.data['authorization_action']['data']
        self.assertEqual(payload['business_number'], '1234')
        self.assertEqual(payload['account_number'], '353535#{}'.format(order_payment.id))
        self.assertEqual(payload['amount'], 250000)
