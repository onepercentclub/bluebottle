from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from rest_framework import status

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.utils import BluebottleTestCase, SessionTestMixin


@override_settings(PAYMENT_METHODS=(
    {
        'provider': 'docdata',
        'id': 'docdata-creditcard',
        'profile': 'creditcard',
        'name': 'CreditCard',
    },
    {
        'provider': 'pledge',
        'id': 'pledge-standard',
        'name': 'Pledge',
        'profile': 'standard',
        'method_access_handler': 'bluebottle.payments_pledge.utils.method_access_handler'
    }
))
class TestPledgePayments(BluebottleTestCase, SessionTestMixin):
    """ Test payments in the context of pledges """

    def setUp(self):
        super(TestPledgePayments, self).setUp()

        self.create_session()

        self.user1 = BlueBottleUserFactory.create(can_pledge=True)
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.order_payment_data = {
            'integration_data': {},
            'payment_method': 'pledgeStandard',
            'meta_data': None,
            'user': None,
            'status': '',
            'updated': None,
            'amount': 25

        }

    def test_create_orderpayment_user_pledge(self):
        """ User that can pledge gets a 201 CREATED"""

        order = OrderFactory.create(user=self.user1, total=10)
        self.order_payment_data['order'] = order.id
        response = self.client.post(reverse('manage-order-payment-list'),
                                    self.order_payment_data,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_orderpayment_user_no_pledge(self):
        """ User that can not pledge gets a 403 FORBIDDEN """

        order = OrderFactory.create(user=self.user2, total=10)
        self.order_payment_data['order'] = order.id
        response = self.client.post(reverse('manage-order-payment-list'),
                                    self.order_payment_data,
                                    token=self.user2_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_orderpayment_and_login(self):
        """
        Anonymous user creates order then logs in as can_pledge user
        should get 201 CREATED
        """

        order = OrderFactory.create(total=10)
        self.order_payment_data['order'] = order.id

        # Set session for anon user
        s = self.session
        s['new_order_id'] = order.pk
        s.save()

        response = self.client.post(reverse('manage-order-payment-list'),
                                    self.order_payment_data,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_orderpayment_anon(self):
        """ Anonymous user gets 401 UNAUTHORIZED """

        order = OrderFactory.create(total=10)
        self.order_payment_data['order'] = order.id

        # Set session for anon user
        s = self.session
        s['new_order_id'] = order.pk
        s.save()

        response = self.client.post(reverse('manage-order-payment-list'),
                                    self.order_payment_data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_payment_methods_pledge_user(self):
        """ Test that pledge users see the correct payment methods """

        response = self.client.get(reverse('payment-method-list'), {'country': 'NL'},
                                   token=self.user1_token)
        results = response.data['results']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 2)
        # Pledge method_access_handler should not be returned in the api
        with self.assertRaises(KeyError):
            results[1]['method_access_handler']

    def test_get_payment_methods_non_pledge_user(self):
        """ Test that non-pledge users see the correct payment methods """

        response = self.client.get(reverse('payment-method-list'), {'country': 'NL'},
                                   token=self.user2_token)
        results = response.data['results']

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results), 1)
