import json
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
        self.manage_donation_list_url = reverse('manage-donation-list')


class TestCreateDonation(OrderApiTestCase):

    def test_create_donation(self):

        # Check that there's no orders
        response = self.client.get(self.manage_order_list_url, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # Create an order
        response = self.client.post(self.manage_order_list_url, {}, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'cart')
        self.assertEqual(response.data['total'], 0)
        order_id = response.data['id']

        # Check that there's one order
        response = self.client.get(self.manage_order_list_url, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        donation1 = {
            "project": self.project1.slug,
            "order": order_id,
            "amount": 35
        }

        response = self.client.post(self.manage_donation_list_url, donation1, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'new')
        donation_id = response.data['id']

        # Check that the order total is equal to the donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 35)

        # Check that this user can change the amount
        donation_url = "{0}{1}".format(self.manage_donation_list_url, donation_id)
        donation1['amount'] = 50
        response = self.client.put(donation_url, json.dumps(donation1), 'application/json', HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the order total is equal to the increased donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 50)

        # Add another donation
        donation2 = {
            "project": self.project2.slug,
            "order": order_id,
            "amount": 47
        }
        response = self.client.post(self.manage_donation_list_url, donation2, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'new')

        # Check that the order total is equal to the two donations
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['donations']), 2)
        self.assertEqual(response.data['total'], 97)

        # remove the first donation
        response = self.client.delete(donation_url, 'application/json', HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that the order total is equal to second donation
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, HTTP_AUTHORIZATION=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['donations']), 1)
        self.assertEqual(response.data['total'], 47)



