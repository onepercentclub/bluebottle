import json
from bluebottle.bb_orders.models import OrderStatuses
from bluebottle.orders.models import Order
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import InitProjectDataMixin
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status


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
        self.assertEqual(response.data['status'], 'new')
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
        self.assertEqual(response.data['status'], 'new')
        self.assertEqual(response.data['total'], 0)
        order_id = response.data['id']

        # User should be able to update the order because status is still 'new'
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.put(order_url, json.dumps({}), 'application/json', HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Change order status to 'locked'
        order = Order.objects.get(pk=order_id)
        order.status = OrderStatuses.locked
        order.save()

        # User should not be able to update the order now that it has status 'locked'
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.put(order_url, json.dumps({}), 'application/json', HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

