import json

from django.test import TestCase
from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory

from ..models import Order


class OrderApiTestCase(TestCase):
    """
    Base class for ``Order`` app API endpoints test cases.
    """
    def setUp(self):
        self.user = BlueBottleUserFactory.create()

        self.project_1 = ProjectFactory.create()
        self.project_2 = ProjectFactory.create()


class TestOrderCreate(OrderApiTestCase):

    def test_create_order(self):
        """
        Tests that the list of project phases can be obtained from its
        endpoint.
        """
        self.client.login(username=self.user.email, password='testing')
        order_url = reverse('order-list')

        response = self.client.get(order_url)
        self.assertEqual(response.status_code, 200)

        # Create an order as authenticated user should return an order with user id set
        response = self.client.post(order_url, {})
        self.assertEqual(response.status_code, 201)
        self.assertEquals(response.data['status'], 'cart')
        self.assertEquals(response.data['user'], self.user.id)

        # Order list should return one item
        response = self.client.get(order_url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.data['count'], 1)

        # As anonymous user order list should return 0 items
        self.client.logout()
        response = self.client.get(order_url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.data['count'], 0)

        # Creating an order as anonymous should have no user set.
        response = self.client.post(order_url, {})
        self.assertEqual(response.status_code, 201)
        self.assertEquals(response.data['status'], 'cart')
        self.assertEquals(response.data['user'], None)

        # Order list should now have 1 item
        response = self.client.get(order_url)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response.data['count'], 1)



