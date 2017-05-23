from django.core.urlresolvers import reverse
from bluebottle.test.utils import BluebottleTestCase
from rest_framework import status
from bluebottle.orders.models import Order
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.payments.services import PaymentService
from bluebottle.payments_mock.adapters import MockPaymentAdapter
from mock import patch

from bluebottle.utils.utils import StatusDefinition


class OrderApiTestCase(BluebottleTestCase):
    def setUp(self):
        super(OrderApiTestCase, self).setUp()

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.country = CountryFactory.create(alpha2_code='NL')

        self.init_projects()
        self.project1 = ProjectFactory.create(amount_asked=5000)
        self.project1.set_status('campaign')

        self.project2 = ProjectFactory.create(amount_asked=3750)
        self.project2.set_status('campaign')

        self.manage_order_list_url = reverse('manage-order-list')


class TestCreateUpdateOrder(OrderApiTestCase):
    def test_create_order(self):
        # Check that there's no orders
        response = self.client.get(self.manage_order_list_url,
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # Create an order
        response = self.client.post(self.manage_order_list_url, {},
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], StatusDefinition.CREATED)
        self.assertEqual(response.data['total']['amount'], 0.00)
        self.assertEqual(response.data['total']['currency'], 'EUR')

        # Check that there's one order
        response = self.client.get(self.manage_order_list_url,
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_update_order(self):
        # Create an order
        response = self.client.post(self.manage_order_list_url, {},
                                    token=self.user1_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], StatusDefinition.CREATED)
        self.assertEqual(response.data['total']['amount'], 0.00)
        self.assertEqual(response.data['total']['currency'], 'EUR')
        order_id = response.data['id']

        # User should be able to update the order because status is still 'new'
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.put(order_url, {}, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Change order status to 'locked'
        order = Order.objects.get(pk=order_id)
        order.locked()
        order.save()

        # User should not be able to update the order now that it has status 'locked'
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.put(order_url, {}, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestOrderPermissions(BluebottleTestCase):
    """ Test the permissions for order ownership in bb_orders """

    def setUp(self):
        super(TestOrderPermissions, self).setUp()

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.order = OrderFactory.create(user=self.user1,
                                         status=StatusDefinition.SUCCESS)
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='mock',
                                                        status=StatusDefinition.SUCCESS)

    def test_user_not_owner(self):
        """ User that is not owner of the order tries to do a get to the order should get a 403"""
        response = self.client.get(
            reverse('manage-order-detail', kwargs={'pk': self.order.pk}),
            token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_is_owner(self):
        """ User that is owner of the order must get a 200 response """
        response = self.client.get(
            reverse('manage-order-detail', kwargs={'pk': self.order.pk}),
            token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestAdditionalOrderPermissions(OrderApiTestCase):
    def setUp(self):
        super(TestAdditionalOrderPermissions, self).setUp()

        self.order = OrderFactory.create(user=self.user1)

    def test_create_for_another_owner(self):
        """ Creating an order for another user should not be possible """
        order_data = {
            "user": self.user2.pk
        }

        response = self.client.post(self.manage_order_list_url, order_data,
                                    token=self.user1_token)
        # Order creation success but the user should be re-set to the current user
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user'], self.user1.pk)

    def test_update_with_another_owner(self):
        """ Updating an order and assigning a different user should not be possible """
        updated_order = {
            "user": self.user2.pk
        }

        response = self.client.put(reverse('manage-order-detail',
                                           kwargs={'pk': self.order.id}),
                                   updated_order,
                                   token=self.user1_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestStatusUpdates(BluebottleTestCase):
    def setUp(self):
        super(TestStatusUpdates, self).setUp()

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

    @patch.object(MockPaymentAdapter, 'check_payment_status')
    def test_no_success_payment_status_check(self, mock_check_payment_status):
        self.order = OrderFactory.create(user=self.user1, total=15)
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='mock')
        self.service = PaymentService(order_payment=self.order_payment)
        self.client.get(reverse('manage-order-detail',
                                kwargs={'pk': self.order.id}),
                        token=self.user1_token)
        self.assertEqual(mock_check_payment_status.called, True)

    @patch.object(MockPaymentAdapter, 'check_payment_status')
    def test_success_payment_status_check(self, mock_check_payment_status):
        self.order = OrderFactory.create(user=self.user1, total=15,
                                         status=StatusDefinition.SUCCESS)
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='mock',
                                                        status=StatusDefinition.AUTHORIZED)

        self.client.get(reverse('manage-order-detail',
                                kwargs={'pk': self.order.id}),
                        token=self.user1_token)
        self.assertEqual(mock_check_payment_status.called, False)
