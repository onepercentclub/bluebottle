from django.test import TestCase
from django.core.urlresolvers import reverse
from rest_framework import status

from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.orders import OrderFactory



class DonationApiTestCase(TestCase):
    """
    Base test class for 'Donation' app API endpoint test cases.
    """

    def setUp(self):

        self.user = BlueBottleUserFactory.create()
        self.project = ProjectFactory.create()
        self.order = OrderFactory.create()


class TestDonationCreate(DonationApiTestCase):

    def test_create_anonymous_donation(self):

        self.client.login(username=self.user.email, password='testing')
        donation_url = reverse('manage-donation-list')

        response = self.client.get(donation_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # create a new anonymous donation
        response = self.client.post(donation_url, {'order': self.order.pk, 'project': self.project.slug, 'amount': 50, 'anonymous': True})


        self.assertEqual(response.status_code, 201)

        # retrieve the donation just created
        donation_url = reverse('manage-donation-detail', kwargs={'pk': response.data['id']})
        response = self.client.get(donation_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check if the anonymous is set to True
        self.assertEqual(True, response.data['anonymous'])

