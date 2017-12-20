from moneyed.classes import Money, KES

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.donations.models import Donation
from bluebottle.payments.models import OrderPayment
from bluebottle.payments_lipisha.adapters import LipishaPaymentAdapter, LipishaPaymentInterface
from bluebottle.payments_lipisha.models import LipishaProject
from bluebottle.payments_lipisha.tests.factory_models import LipishaProjectFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
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


@override_settings(**lipisha_settings)
class LipishaInitiatePaymentViewTestCase(BluebottleTestCase):
    def setUp(self):
        self.project = ProjectFactory.create()
        LipishaProjectFactory.create(project=self.project, account_number='424242')
        self.interface = LipishaPaymentInterface()
        self.order = OrderFactory.create()
        self.donation = DonationFactory.create(
            amount=Money(1500, KES),
            order=self.order,
            project=self.project
        )
        self.order_payment = OrderPaymentFactory.create(
            payment_method='lipishaMpesa',
            order=self.order
        )
        self.adapter = LipishaPaymentAdapter(self.order_payment)
        self.lipisha_update_url = reverse('lipisha-update-payment')

    def test_create_donation_from_lipisha_call(self):
        data = {
            'api_key': '1234567890',
            'api_signature': '9784904749074987dlndflnlfgnh',
            'api_version': '2.0.0',
            'api_type': 'Initiate',
            'transaction_account': '424242',
            'transaction_account_number': '424242',
            'transaction_merchant_reference': '',
            'transaction': '7ACCB5CC8',
            'transaction_reference': '7ACCB5CC8',
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Completed',
            'transaction_mobile': '25471000000',
            'transaction_type': 'Payment'
        }
        response = self.client.post(self.lipisha_update_url, data)
        expected = {
            'transaction_status_code': '001',
            'transaction_status_description': 'Transaction received successfully.',
            'api_key': '1234567890',
            'transaction_status': 'SUCCESS',
            'transaction_custom_sms': 'Dear Sam Gichuru, thanks for your donation 7ACCB5CC8 '
                                      'of KES 1750 to {}!'.format(self.project.title),
            'transaction_status_action': 'ACCEPT',
            'transaction_reference': '7ACCB5CC8',
            'transaction_status_reason': 'VALID_TRANSACTION',
            'api_version': '1.0.4',
            'api_type': 'Receipt'
        }

        # There should be a new donation for this project
        donation = Donation.objects.order_by('-id').first()
        self.assertEqual(donation.project, self.project)
        self.assertEqual(donation.status, 'pending')
        self.assertEqual(donation.amount.amount, 1750.00)
        self.assertEqual(donation.name, 'Sam Gichuru')

        # Check that the response is confirm the specification by Lipisha
        self.assertEqual(response.json()['api_key'], expected['api_key'])
        self.assertEqual(response.json()['transaction_status_action'], expected['transaction_status_action'])
        self.assertEqual(response.json()['transaction_reference'], expected['transaction_reference'])
        self.assertEqual(response.json()['transaction_custom_sms'], expected['transaction_custom_sms'])
        self.assertEqual(response.json()['api_type'], expected['api_type'])

        # Now play acknowledge request
        data = {
            'api_key': '1234567890',
            'api_signature': '9784904749074987dlndflnlfgnh',
            'api_version': '2.0.0',
            'api_type': 'Acknowledge',
            'transaction_account': '424242',
            'transaction_account_number': '424242',
            'transaction_merchant_reference': '',
            'transaction': '7ACCB5CC8',
            'transaction_reference': '7ACCB5CC8',
            'transaction_amount': '1750',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Success',
            'transaction_mobile': '25471000000',
            'transaction_type': 'Payment'
        }
        response = self.client.post(self.lipisha_update_url, data)
        expected = {
            'transaction_status_code': '001',
            'transaction_status_description': 'Transaction received successfully.',
            'api_key': '1234567890',
            'transaction_status': 'SUCCESS',
            'transaction_custom_sms': 'Dear Sam Gichuru, thanks for your donation 7ACCB5CC8 '
                                      'of KES 1750 to {}!'.format(self.project.title),
            'transaction_status_action': 'ACCEPT',
            'transaction_reference': '7ACCB5CC8',
            'transaction_status_reason': 'VALID_TRANSACTION',
            'api_version': '1.0.4',
            'api_type': 'Receipt'
        }

        # There should be a new donation for this project
        donation = Donation.objects.order_by('-id').first()
        self.assertEqual(donation.project, self.project)
        self.assertEqual(donation.status, 'success')
        self.assertEqual(donation.amount.amount, 1750.00)
        self.assertEqual(donation.name, 'Sam Gichuru')

        # Check that the response is confirm the specification by Lipisha
        self.assertEqual(response.json()['api_key'], expected['api_key'])
        self.assertEqual(response.json()['transaction_status_action'], expected['transaction_status_action'])
        self.assertEqual(response.json()['transaction_reference'], '7ACCB5CC8')
        self.assertEqual(response.json()['transaction_custom_sms'], expected['transaction_custom_sms'])
        self.assertEqual(response.json()['api_type'], expected['api_type'])


@override_settings(**lipisha_settings)
class LipishaProjectAddOnTest(BluebottleTestCase):
    """
    Integration tests for the Project Add-On API.
    """

    def setUp(self):
        super(LipishaProjectAddOnTest, self).setUp()
        self.init_projects()
        self.project = ProjectFactory()
        self.project_url = reverse('project_detail', args=[self.project.slug])

    def test_addon_api(self):
        # Test that the project has no add-ons yet
        response = self.client.get(self.project_url)
        self.assertEqual(len(response.data['addons']), 0)

        # Add a Lipisha code
        LipishaProject.objects.create(project=self.project,
                                      account_number='456789')

        # Test the project now has the Lipisha add-on
        response = self.client.get(self.project_url)
        self.assertEqual(len(response.data['addons']), 1)
        self.assertEqual(response.data['addons'][0]['type'], 'mpesa')
        self.assertEqual(response.data['addons'][0]['account_number'], '456789')
        self.assertEqual(response.data['addons'][0]['paybill_number'], '1234')
