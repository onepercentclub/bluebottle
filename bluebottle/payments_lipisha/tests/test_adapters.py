from bluebottle.donations.models import Donation
from bluebottle.payments.exception import PaymentException
from moneyed.classes import Money, KES
from mock import patch

from django.test.utils import override_settings

from bluebottle.payments_lipisha.adapters import LipishaPaymentAdapter, LipishaPaymentInterface
from bluebottle.payments_lipisha.tests.factory_models import LipishaProjectFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.projects import ProjectFactory
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

    def setUp(self):
        self.order = OrderFactory.create()
        DonationFactory.create(amount=Money(1500, KES), order=self.order)
        self.order_payment = OrderPaymentFactory.create(
            payment_method='lipishaMpesa',
            order=self.order
        )
        self.adapter = LipishaPaymentAdapter(self.order_payment)

    @patch('bluebottle.payments_lipisha.adapters.Lipisha')
    def test_create_success_payment(self, mock_client):
        """
        Test Lipisha M-PESA payment that turns to success.
        """

        authorization_action = self.adapter.get_authorization_action()

        self.assertEqual(int(self.adapter.payment.reference), self.order_payment.id)

        self.assertEqual(authorization_action, {
            'payload': {
                'account_number': '353535#{}'.format(self.order_payment.id),
                'amount': 1500,
                'business_number': '1234'
            },
            'type': 'process'
        })

        # Now confirm the payment by user and have Lipisha send a success
        instance = mock_client.return_value
        instance.get_transactions.return_value = lipisha_success_response

        self.order_payment.integration_data = {}
        adapter = LipishaPaymentAdapter(self.order_payment)
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
        authorization_action = self.adapter.get_authorization_action()

        self.assertEqual(int(self.adapter.payment.reference), self.order_payment.id)

        self.assertEqual(authorization_action, {
            'payload': {
                'account_number': '353535#{}'.format(self.order_payment.id),
                'amount': 1500,
                'business_number': '1234'
            },
            'type': 'process'
        })

        # Now confirm the payment by user and have Lipisha send a not-found
        # we should receive an exception
        instance = mock_client.return_value
        instance.get_transactions.return_value = lipisha_not_found_response

        self.order_payment.integration_data = {}
        adapter = LipishaPaymentAdapter(self.order_payment)

        with self.assertRaises(PaymentException):
            adapter.check_payment_status()


@override_settings(**lipisha_settings)
class LipishaPaymentInterfaceTestCase(BluebottleTestCase):
    def setUp(self):
        self.project = ProjectFactory.create()
        self.interface = LipishaPaymentInterface()
        LipishaProjectFactory.create(project=self.project, account_number='424242')
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

    def test_update_donation_from_lipisha_call(self):
        data = {
            'transaction_account_number': '424242',
            'transaction_merchant_reference': self.order_payment.id,
            'transaction_reference': '',
            'transaction_amount': '2500',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Completed',
            'transaction_mobile': '25471000000'
        }
        self.interface.initiate_payment(data)
        donation = Donation.objects.get(pk=self.donation.pk)
        self.assertEqual(donation.status, 'success')
        # Amount should be updated
        self.assertEqual(donation.amount.amount, 2500.00)

    def test_create_donation_from_lipisha_call(self):
        data = {
            'transaction_account_number': '424242',
            'transaction_merchant_reference': '',
            'transaction_reference': '',
            'transaction_amount': '3500',
            'transaction_currency': 'KES',
            'transaction_name': 'SAM+GICHURU',
            'transaction_status': 'Completed',
            'transaction_mobile': '25471000000'
        }
        self.interface.initiate_payment(data)
        # Old donation should not be touched
        old_donation = Donation.objects.get(pk=self.donation.pk)
        self.assertEqual(old_donation.status, 'locked')

        # There should be a new donation for this project
        donation = Donation.objects.order_by('-id').first()
        self.assertEqual(donation.project, self.project)
        self.assertEqual(donation.status, 'success')
        self.assertEqual(donation.amount.amount, 3500.00)
        self.assertEqual(donation.name, 'Sam Gichuru')

# Test for updating a payment create by normal donation flow
# - Test it finds the payment and updates
# - Test it updates amounts for donation, order, order payment and project

# Test create new donation / payment from direct M-Pesa payment
# - Test it won't generate twice for one code
# - Test all amounts are set correctly for donation, order, order payment and project

# Test it handles reversed payments correctly
# - Test status changes correctly (order, order payment and payment)
# - Test all amounts are set correctly for donation, order, order payment and project
