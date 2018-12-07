from mock import patch

from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from rest_framework import status

from bluebottle.payments_mock.adapters import MockPaymentAdapter
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.utils import BluebottleTestCase

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.payouts import (
    StripePayoutAccountFactory, PlainPayoutAccountFactory
)


class TestOrderPaymentPermissions(BluebottleTestCase):
    """ Test the permissions for order ownership in bb_orders """

    def setUp(self):
        super(TestOrderPaymentPermissions, self).setUp()

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.order = OrderFactory.create(user=self.user1, total=10)

        self.order_payment_data = {
            'order': self.order.id,
            'integration_data': {'issuerId': 'huey'},
            'payment_method': 'mockIdeal',
            'meta_data': None,
            'user': None,
            'status': '',
            'updated': None,
            'amount': 25

        }

    @patch.object(MockPaymentAdapter, 'create_payment')
    def test_create_orderpayment_user_owner(self, mock_create_payment):
        """ User that is owner of the order tries to create an order payment gets a 201 CREATED"""

        response = self.client.post(reverse('manage-order-payment-list'),
                                    self.order_payment_data,
                                    token=self.user1_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_orderpayment_user_not_owner(self):
        """ User that is not owner of the order tries to create an order payment gets 403"""
        response = self.client.post(reverse('manage-order-payment-list'),
                                    self.order_payment_data,
                                    token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_payment_methods_unauthenticated(self):
        """ Test that  unauthenticated users may retrieve payment methods """
        response = self.client.get(reverse('payment-method-list'), {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_payment_methods_authenticated(self):
        """ Test that authenticated users may retrieve payment methods """
        response = self.client.get(reverse('payment-method-list'), {},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_payment_methods_for_country(self):
        """ Test that passing a country will restrict the payment methods """

        # Check that NL shows 3 methods (including iDEAL)
        response = self.client.get(reverse('payment-method-list'),
                                   {'country': 'NL'},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['country'], 'NL')
        self.assertEqual(len(response.data['results']), 3)

        # Check that BG is showing only 2 methods
        response = self.client.get(reverse('payment-method-list'),
                                   {'country': 'BG'},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['country'], 'BG')
        self.assertEqual(len(response.data['results']), 2)

        # Check that not specifying a country whos all methods
        response = self.client.get(reverse('payment-method-list'), {},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['country'], None)
        self.assertEqual(len(response.data['results']), 3)

    @patch('bluebottle.payments.views.get_ip')
    @override_settings(SKIP_IP_LOOKUP=False)
    def test_get_payment_methods_for_ip(self, get_ip):
        """ Test that passing a IP will restrict the payment methods """

        # Zimbawian IP should show 2 methods
        get_ip.return_value = '41.220.16.16'
        response = self.client.get(reverse('payment-method-list'), {},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['country'], 'ZW')
        self.assertEqual(len(response.data['results']), 2)

        # Dutch IP should show 3 methods
        get_ip.return_value = '213.127.165.114'
        response = self.client.get(reverse('payment-method-list'), {},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data['country'], 'NL')
        self.assertEqual(len(response.data['results']), 3)

    @override_settings(
        PAYMENT_METHODS=[
            {
                'provider': 'stripe',
                'id': 'stripe-creditcard',
                'profile': 'creditcard',
                'name': 'CreditCard',
                'currencies': {'EUR': {'min_amount': 5, 'max_amount': 1000}}
            }, {
                'provider': 'docdata',
                'id': 'docdata-directdebit',
                'profile': 'directdebit',
                'name': 'DirectDebit',
                'currencies': {'EUR': {'min_amount': 5, 'max_amount': 1000}}
            }, {
                'provider': 'pledge',
                'id': 'pledge',
                'profile': 'pledge',
                'name': 'Pledge',
                'currencies': {'EUR': {'min_amount': 5, }}
            },
        ]
    )
    def test_get_payment_methods_stripe_project(self):
        """ Test that passing a IP will restrict the payment methods """
        project = ProjectFactory.create(
            payout_account=StripePayoutAccountFactory.create()
        )

        response = self.client.get(
            reverse('payment-method-list'),
            {'project_id': project.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        providers = [method['provider'] for method in response.data['results']]
        self.assertTrue('stripe' in providers)
        self.assertTrue('pledge' in providers)

    @override_settings(
        PAYMENT_METHODS=[
            {
                'provider': 'stripe',
                'id': 'stripe-creditcard',
                'profile': 'creditcard',
                'name': 'CreditCard',
                'currencies': {'EUR': {'min_amount': 5, 'max_amount': 1000}}
            }, {
                'provider': 'docdata',
                'id': 'docdata-directdebit',
                'profile': 'directdebit',
                'name': 'DirectDebit',
                'currencies': {'EUR': {'min_amount': 5, 'max_amount': 1000}}
            }, {
                'provider': 'pledge',
                'id': 'pledge',
                'profile': 'pledge',
                'name': 'Pledge',
                'currencies': {'EUR': {'min_amount': 5, }}
            },
        ]
    )
    def test_get_payment_methods_plain_project(self):
        """ Test that passing a IP will restrict the payment methods """
        project = ProjectFactory.create(
            payout_account=PlainPayoutAccountFactory.create()
        )

        response = self.client.get(
            reverse('payment-method-list'),
            {'project_id': project.pk}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

        providers = [method['provider'] for method in response.data['results']]
        self.assertTrue('docdata' in providers)
        self.assertTrue('pledge' in providers)
