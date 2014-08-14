from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import InitProjectDataMixin
from django.core.urlresolvers import reverse
from django.test import TestCase
from rest_framework import status


class OrderApiTestCase(InitProjectDataMixin, TestCase):

    def setUp(self):
        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        CountryFactory.create(alpha2_code='NL')

        self.init_projects()
        self.project = ProjectFactory.create(amount_asked=5000)
        self.project.set_status('campaign')

        self.manage_order_list_url = reverse('manage-order-list')
        self.manage_donation_list_url = reverse('manage-donation-list')


class TestCreateDonation(OrderApiTestCase):

    def test_create_donation(self):

        # Check that there's no orders
        response = self.client.get(self.manage_order_list_url, HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

        # Create an order
        response = self.client.post(self.manage_order_list_url, {}, HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'cart')
        self.assertEqual(response.data['total'], 0)
        order_id = response.data['id']

        # Check that there's one order
        response = self.client.get(self.manage_order_list_url, HTTP_AUTHORIZATION=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        donation = {
            'project': self.project.slug,
            'order': order_id,
            'amount': 35
        }

        response = self.client.post(self.manage_donation_list_url, donation, HTTP_AUTHORIZATION=self.user_token)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(response.data['status'], DonationStatuses.new)
        # donation_id = response.data['id']
        #
        # # Check that the order total is equal to the donation amount
        # order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        # response = self.client.get(order_url, HTTP_AUTHORIZATION=self.user_token)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        # self.assertEqual(response.data['total'], donation['amount'])

