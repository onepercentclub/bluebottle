import json
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status
from bluebottle.orders.models import Order
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.payments import OrderPaymentFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.utils import InitProjectDataMixin
from bluebottle.utils.model_dispatcher import get_order_model
from bluebottle.payments.services import PaymentService
from bluebottle.payments_mock.adapters import MockPaymentAdapter
from mock import patch

from bluebottle.utils.utils import StatusDefinition

ORDER_MODEL = get_order_model()


class OrderApiTestCase(InitProjectDataMixin, TestCase):

    def setUp(self):
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
        response = self.client.get(self.manage_order_list_url, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # Create an order
        response = self.client.post(self.manage_order_list_url, {}, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], StatusDefinition.CREATED)
        self.assertEqual(response.data['total'], 0)
        order_id = response.data['id']

        # Check that there's one order
        response = self.client.get(self.manage_order_list_url, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_update_order(self):

        # Create an order
        response = self.client.post(self.manage_order_list_url, {}, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], StatusDefinition.CREATED)
        self.assertEqual(response.data['total'], 0)
        order_id = response.data['id']

        # User should be able to update the order because status is still 'new'
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.put(order_url, json.dumps({}), 'application/json', HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Change order status to 'locked'
        order = Order.objects.get(pk=order_id)
        order.locked()

        # User should not be able to update the order now that it has status 'locked'
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.put(order_url, json.dumps({}), 'application/json', HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestStatusUpdates(TestCase):
    def setUp(self):
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

    @patch.object(MockPaymentAdapter, 'check_payment_status')
    def test_no_success_payment_status_check(self, mock_check_payment_status):
        self.skip("For some reason the status of the payment is NULL in tests when saving")
        self.order = OrderFactory.create(user=self.user1)
        self.order_payment = OrderPaymentFactory.create(order=self.order, payment_method='mock')
        self.service = PaymentService(order_payment=self.order_payment)
        response = self.client.get(reverse('manage-order-detail', kwargs={'pk': self.order.id}),
                                   HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(mock_check_payment_status.called, True)

    @patch.object(MockPaymentAdapter, 'check_payment_status')
    def test_success_payment_status_check(self, mock_check_payment_status):
        self.skip("For some reason the status of the payment is NULL in tests when saving")
        self.order = OrderFactory.create(user=self.user1, status=StatusDefinition.SUCCESS)
        self.order_payment = OrderPaymentFactory.create(order=self.order,
                                                        payment_method='mock',
                                                        status=StatusDefinition.AUTHORIZED)

        response = self.client.get(reverse('manage-order-detail', kwargs={'pk': self.order.id}),
                                   HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(mock_check_payment_status.called, False)
