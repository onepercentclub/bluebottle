from django.test.utils import override_settings
from mock import patch

from decimal import Decimal
from django.core.urlresolvers import reverse

from rest_framework import status

from moneyed import Money

from bluebottle.bb_orders.views import ManageOrderDetail
from bluebottle.donations.models import Donation, DonationPlatformSettings, DonationDefaultAmounts
from bluebottle.orders.models import Order
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.fundraisers import FundraiserFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.rewards import RewardFactory
from bluebottle.test.utils import BluebottleTestCase, SessionTestMixin
from bluebottle.utils.utils import StatusDefinition


@override_settings(
    PAYMENT_METHODS=[
        {
            'provider': 'docdata',
            'id': 'docdata-ideal',
            'profile': 'ideal',
            'name': 'iDEAL',
            'restricted_countries': ('NL', ),
            'supports_recurring': False,
            'currencies': {
                'EUR': {'min_amount': 5, 'max_amount': 100},
                'USD': {'min_amount': 5, 'max_amount': 100},
                'NGN': {'min_amount': 5, 'max_amount': 100},
            }
        }]
)
class DonationApiTestCase(BluebottleTestCase, SessionTestMixin):
    def setUp(self):
        super(DonationApiTestCase, self).setUp()

        self.create_session()

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.init_projects()

        self.project1 = ProjectFactory.create(amount_asked=5000)
        self.project1.set_status('campaign')

        self.project2 = ProjectFactory.create(amount_asked=3750)
        self.project2.set_status('campaign')

        self.manage_order_list_url = reverse('order-manage-list')
        self.manage_donation_list_url = reverse('manage-donation-list')

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create(is_co_financer=True)
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.project = ProjectFactory.create()
        self.order = OrderFactory.create(user=self.user)

        self.dollar_project = ProjectFactory.create(currencies=['USD'])
        self.multi_project = ProjectFactory.create(currencies=['EUR', 'USD', 'NGN'])


# Mock the ManageOrderDetail check_status_psp function which will request status_check at PSP
@patch.object(ManageOrderDetail, 'check_status_psp')
class TestDonationPermissions(DonationApiTestCase):
    def test_user_is_order_owner(self, mock_check_status_psp):
        """ Test that a user that is owner of the order can post a new donation """
        donation1 = {
            "project": self.project.slug,
            "order": self.order.id,
            "amount": 35
        }

        self.assertEqual(Donation.objects.count(), 0)
        response = self.client.post(reverse('manage-donation-list'), donation1,
                                    token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Donation.objects.count(), 1)

    def test_user_is_not_order_owner(self, mock_check_status_psp):
        """ Test that a user who is not owner of an order cannot create a new donation """

        donation1 = {
            "project": self.project.slug,
            "order": self.order.id,
            "amount": 35
        }

        self.assertEqual(Donation.objects.count(), 0)
        response = self.client.post(reverse('manage-donation-list'), donation1,
                                    token=self.user2_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Donation.objects.count(), 0)

    def test_order_status_not_new(self, mock_check_status_psp):
        """ Test that a non-new order status produces a forbidden response """

        order = OrderFactory.create(user=self.user,
                                    status=StatusDefinition.SUCCESS)

        donation1 = {
            "project": self.project.slug,
            "order": order.id,
            "amount": 35
        }

        self.assertEqual(Donation.objects.count(), 0)
        response = self.client.post(reverse('manage-donation-list'), donation1,
                                    token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Donation.objects.count(), 0)

    def test_order_status_new(self, mock_check_status_psp):
        """ Test that a new order status produces a 201 created response """

        order = OrderFactory.create(user=self.user,
                                    status=StatusDefinition.CREATED)

        donation1 = {
            "project": self.project.slug,
            "order": order.id,
            "amount": 35
        }

        self.assertEqual(Donation.objects.count(), 0)
        response = self.client.post(reverse('manage-donation-list'), donation1,
                                    token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Donation.objects.count(), 1)

    def test_currency_does_match_project(self, mock_check_status_psp):
        """ Test that a user who is not owner of an order cannot create a new donation """

        donation = {
            "project": self.project.slug,
            "order": self.order.id,
            "amount": {'currency': 'USD', 'amount': 35}
        }

        response = self.client.post(reverse('manage-donation-list'), donation,
                                    token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Donation.objects.count(), 0)

        donation = {
            "project": self.dollar_project.slug,
            "order": self.order.id,
            "amount": {'currency': 'USD', 'amount': 35}
        }

        response = self.client.post(reverse('manage-donation-list'), donation,
                                    token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        donation = {
            "project": self.multi_project.slug,
            "order": self.order.id,
            "amount": {'currency': 'USD', 'amount': 35}
        }

        response = self.client.post(reverse('manage-donation-list'), donation,
                                    token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_donation_update_not_same_owner(self, mock_check_status_psp):
        """ Test that an update to a donation where the user is not the owner produces a 403"""

        donation = DonationFactory(order=self.order, amount=35)

        updated_donation = {
            "project": self.project.slug,
            "order": self.order.id,
            "amount": 50
        }

        self.assertEqual(Donation.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user2_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Donation.objects.count(), 1)

    def test_donation_update_same_owner(self, mock_check_status_psp):
        """ Test that an update to a donation where the user is the owner produces a 200 OK"""

        donation = DonationFactory(order=self.order, amount=35)

        updated_donation = {
            "project": self.project.slug,
            "order": self.order.id,
            "amount": 50
        }

        self.assertEqual(Donation.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Donation.objects.count(), 1)

    def test_donation_update_order_not_new(self, mock_check_status_psp):
        """ Test that an update to a donation where the order does not have status CREATED produces 403 FORBIDDEN"""

        order = OrderFactory.create(user=self.user,
                                    status=StatusDefinition.SUCCESS)

        donation = DonationFactory(order=order, amount=35)

        updated_donation = {
            "project": self.project.slug,
            "order": order.id,
            "amount": 50
        }

        self.assertEqual(Donation.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Donation.objects.count(), 1)

    def test_donation_update_order_new(self, mock_check_status_psp):
        """ Test that an update to a donation where the order does has status CREATED produces 200 OK response"""

        order = OrderFactory.create(user=self.user,
                                    status=StatusDefinition.CREATED)

        donation = DonationFactory(order=order, amount=35)

        updated_donation = {
            "project": self.project.slug,
            "order": order.id,
            "amount": 50
        }

        self.assertEqual(Donation.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Donation.objects.count(), 1)

    def test_donation_update_order_change_currency(self, mock_check_status_psp):
        """ Test that an update to a donation where the order does has status CREATED produces 200 OK response"""

        order = OrderFactory.create(user=self.user,
                                    status=StatusDefinition.CREATED)

        donation = DonationFactory(order=order, amount=Money(100, 'USD'))

        updated_donation = {
            "project": donation.project.slug,
            "order": order.id,
            "amount": {'amount': 200, 'currency': 'EUR'}
        }

        self.assertEqual(Donation.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Donation.objects.count(), 1)

        self.assertEqual(response.data['amount'], {'currency': 'EUR', 'amount': Decimal(200)})


# Mock the ManageOrderDetail check_status_psp function which will request status_check at PSP
@patch.object(ManageOrderDetail, 'check_status_psp')
class TestCreateDonation(DonationApiTestCase):
    def test_create_single_donation(self, check_status_psp):
        """
        Test donation in the current donation flow where we have just one donation that can't be deleted.
        """

        # Create an order
        response = self.client.post(self.manage_order_list_url, {},
                                    token=self.user1_token)
        order_id = response.data['id']

        fundraiser = FundraiserFactory.create(amount=100)

        donation1 = {
            "fundraiser": fundraiser.pk,
            "project": fundraiser.project.slug,
            "order": order_id,
            "amount": 50
        }

        response = self.client.post(self.manage_donation_list_url, donation1,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'created')

        # Check that the order total is equal to the donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total']['amount'], 50.00)
        self.assertEqual(response.data['total']['currency'], 'EUR')
        self.assertEqual(response.data['donations'][0]['name'], None)

    def test_create_donations_with_names(self, check_status_psp):
        """
        Test donation with specifying a custom donor name.
        """

        # Create an order
        response = self.client.post(self.manage_order_list_url, {},
                                    token=self.user1_token)
        order_id = response.data['id']

        fundraiser = FundraiserFactory.create(amount=100)

        donation1 = {
            "fundraiser": fundraiser.pk,
            "project": fundraiser.project.slug,
            "order": order_id,
            "name": 'Tante Sjaan',
            "amount": 7.5
        }
        donation2 = {
            "fundraiser": fundraiser.pk,
            "project": fundraiser.project.slug,
            "order": order_id,
            "name": 'Ome Piet',
            "amount": 12.5
        }

        response = self.client.post(self.manage_donation_list_url, donation1,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(self.manage_donation_list_url, donation2,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check that the order total is equal to the donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total']['amount'], 20.00)
        self.assertEqual(response.data['total']['currency'], 'EUR')
        self.assertEqual(response.data['donations'][1]['name'], 'Tante Sjaan')
        self.assertEqual(response.data['donations'][0]['name'], 'Ome Piet')

    def test_create_fundraiser_donation(self, check_status_psp):
        """
        Test donation in the current donation flow where we have just one donation that can't be deleted.
        """

        # Create an order
        response = self.client.post(self.manage_order_list_url, {},
                                    token=self.user1_token)
        order_id = response.data['id']

        donation1 = {
            "project": self.project1.slug,
            "order": order_id,
            "amount": 35
        }

        response = self.client.post(self.manage_donation_list_url, donation1,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'created')

        # Check that the order total is equal to the donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total']['amount'], 35.00)

    def test_crud_multiple_donations(self, check_status_psp):
        """
        Test more advanced modifications to donations and orders that aren't currently supported by our
        front-en but
        """

        # Create an order
        response = self.client.post(self.manage_order_list_url, {},
                                    token=self.user1_token)
        order_id = response.data['id']

        donation1 = {
            "project": self.project1.slug,
            "order": order_id,
            "amount": 35
        }

        response = self.client.post(self.manage_donation_list_url, donation1,
                                    token=self.user1_token)
        donation_id = response.data['id']

        # Check that the order total is equal to the donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total']['amount'], 35.00)
        self.assertEqual(response.data['total']['currency'], 'EUR')

        # Check that this user can change the amount
        donation_url = "{0}{1}".format(self.manage_donation_list_url,
                                       donation_id)
        donation1['amount'] = 50
        response = self.client.put(donation_url, donation1,
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the order total is equal to the increased donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total']['amount'], 50.00)
        self.assertEqual(response.data['total']['currency'], 'EUR')

        # Add another donation
        donation2 = {
            "project": self.project2.slug,
            "order": order_id,
            "amount": 47
        }
        response = self.client.post(self.manage_donation_list_url, donation2,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'created')

        # Check that the order total is equal to the two donations
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['donations']), 2)
        self.assertEqual(response.data['total']['amount'], 97.00)
        self.assertEqual(response.data['total']['currency'], 'EUR')

        # remove the first donation
        response = self.client.delete(donation_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that the order total is equal to second donation
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['donations']), 1)
        self.assertEqual(response.data['total']['amount'], 47.00)
        self.assertEqual(response.data['total']['currency'], 'EUR')

        # Set order to status 'locked'
        order = Order.objects.get(id=order_id)
        order.locked()
        order.save()

        donation3 = {
            "project": self.project1.slug,
            "order": order_id,
            "amount": 70
        }

        # Should not be able to add more donations to this order now.
        response = self.client.post(self.manage_donation_list_url, donation3,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Check that this user can't change the amount of an donation
        donation1['amount'] = 5
        response = self.client.put(donation_url, donation1,
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_reward_lower_donation_amount(self, check_status_psp):
        """
        Test donation in the current donation flow where we have just one donation that can't be deleted.
        """

        # Create an order
        response = self.client.post(self.manage_order_list_url, {},
                                    token=self.user1_token)
        order_id = response.data['id']

        reward = RewardFactory.create(project=self.project, amount=100)

        donation = {
            "reward": reward.pk,
            "project": self.project.slug,
            "order": order_id,
            "amount": 50
        }

        response = self.client.post(self.manage_donation_list_url, donation,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            'less than the reward amount' in response.data['non_field_errors'][0]
        )

    def test_create_reward_different_currency(self, check_status_psp):
        """
        Test donation in the current donation flow where we have just one donation that can't be deleted.
        """
        self.project.currencies = ['EUR', 'USD']
        self.project.save()

        # Create an order
        response = self.client.post(self.manage_order_list_url, {},
                                    token=self.user1_token)

        order_id = response.data['id']
        reward = RewardFactory.create(project=self.project, amount=100)

        donation = {
            "reward": reward.pk,
            "project": self.project.slug,
            "order": order_id,
            "amount": {'amount': 200, 'currency': 'USD'}
        }

        response = self.client.post(self.manage_donation_list_url, donation,
                                    token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            'must match reward currency' in response.data['non_field_errors'][0]
        )


class TestAnonymousAuthenicatedDonationCreate(DonationApiTestCase):
    def test_create_anonymous_donation(self):
        donation_url = reverse('manage-donation-list')

        # create a new anonymous donation
        response = self.client.post(donation_url, {'order': self.order.pk,
                                                   'project': self.project.slug,
                                                   'amount': 50,
                                                   'name': 'test-name',
                                                   'anonymous': True},
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)

        # retrieve the donation just created
        donation_id = response.data['id']
        donation_url = reverse('manage-donation-detail',
                               kwargs={'pk': donation_id})
        response = self.client.get(donation_url, token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the anonymous is set to True
        self.assertEqual(True, response.data['anonymous'])

        # Set the order to success
        self.order.locked()
        self.order.save()
        self.order.success()
        self.order.save()

        # retrieve the donation through public API
        donation_url = reverse('donation-detail', kwargs={'pk': donation_id})
        response = self.client.get(donation_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that user is NOT shown in public API
        self.assertEqual(None, response.data['user'])
        self.assertEqual(None, response.data['name'])


class TestUnauthenticatedDonationCreate(DonationApiTestCase):
    def setUp(self):
        super(TestUnauthenticatedDonationCreate, self).setUp()

        self.order_anon = OrderFactory.create()

        s = self.session
        s['new_order_id'] = self.order_anon.pk
        s.save()

    def test_create_anonymous_donation(self):
        donation_url = reverse('manage-donation-list')

        # create a new anonymous donation
        response = self.client.post(donation_url, {'order': self.order_anon.pk,
                                                   'project': self.project.slug,
                                                   'amount': 50,
                                                   'anonymous': True})
        self.assertEqual(response.status_code, 201)


@patch.object(ManageOrderDetail, 'check_status_psp')
class TestProjectDonationList(DonationApiTestCase):
    """
    Test that the project donations list only works for the project owner
    """

    def setUp(self):
        super(TestProjectDonationList, self).setUp()

        self.project3 = ProjectFactory.create(amount_asked=5000,
                                              owner=self.user1)
        self.project3.set_status('campaign')

        order = OrderFactory.create(user=self.user1, status=StatusDefinition.SUCCESS)
        self.donation = DonationFactory.create(
            amount=1000, project=self.project3, order=order
        )

        self.project_donation_list_url = reverse('project-donation-list')

    def test_project_donation_list(self, check_status_psp):
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        donation = response.data['results'][0]
        self.assertEqual(donation['amount']['amount'], 1000.00)
        self.assertEqual(donation['amount']['currency'], 'EUR')
        self.assertEqual(donation['project'], self.project3.id)

    def test_project_donation_failed(self, check_status_psp):
        self.donation.order.transition_to('failed')
        self.order.save()
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_project_donation_cancelled(self, check_status_psp):
        self.donation.order.transition_to('refunded')
        self.donation.order.transition_to('cancelled')
        self.order.save()
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_successful_project_donation_list(self, check_status_psp):
        donation_settings = DonationPlatformSettings.load()
        donation_settings.show_donation_amount = True
        donation_settings.save()

        # Unsuccessful donations should not be shown
        order = OrderFactory.create(user=self.user2)
        reward = RewardFactory.create(project=self.project3)
        DonationFactory.create(amount=2000, project=self.project3, reward=reward,
                               order=order)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1,
                         'Only the successful donation should be returned')
        self.assertIn('amount', response.data['results'][0])
        self.assertIn('reward', response.data['results'][0])

    def test_project_donation_list_without_amounts(self, check_status_psp):
        donation_settings = DonationPlatformSettings.load()
        donation_settings.show_donation_amount = False
        donation_settings.save()
        reward = RewardFactory.create(project=self.project3)
        order = OrderFactory.create(user=self.user2)
        DonationFactory.create(amount=2000, project=self.project3, reward=reward,
                               order=order)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1,
                         'Only the successful donation should be returned')
        self.assertNotIn('amount', response.data['results'][0])
        self.assertNotIn('reward', response.data['results'][0])

    def test_successful_project_donation_list_paged(self, check_status_psp):
        for i in range(30):
            order = OrderFactory.create(user=self.user1, status=StatusDefinition.SUCCESS)
            DonationFactory.create(amount=2000, project=self.project3,
                                   order=order)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 31,
                         'All the donations should be returned')
        self.assertEqual(len(response.data['results']), 20)

    def test_project_donation_list_co_financing(self, check_status_psp):
        order = OrderFactory.create(user=self.user2, status=StatusDefinition.SUCCESS)
        DonationFactory.create(amount=1500, project=self.project3,
                               order=order)

        anonymous_order = OrderFactory.create(status=StatusDefinition.SUCCESS)
        DonationFactory.create(amount=1000, project=self.project3,
                               order=anonymous_order, anonymous=True)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug, 'co_financing': 'true'},
                                   token=self.user1_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1,
                         'Only donations by co-financers should be returned')
        self.assertEqual(response.data['results'][0]['amount']['amount'], 1500.00)

    def test_project_donation_list_co_financing_is_false(self, check_status_psp):
        # Co_financing order and donation
        order = OrderFactory.create(user=self.user2, status=StatusDefinition.SUCCESS)
        DonationFactory.create(amount=1500, project=self.project3,
                               order=order)

        # Anonymous order and donation
        OrderFactory.create(status=StatusDefinition.SUCCESS)
        DonationFactory.create(amount=1500, project=self.project3,
                               order=order, anonymous=True)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug, 'co_financing': 'false'},
                                   token=self.user1_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2,
                         'Only donations and anonymous donations should be returned')
        self.assertEqual(response.data['results'][0]['amount']['amount'], 1500.00)
        self.assertEqual(response.data['results'][1]['amount']['amount'], 1000.00)

    def test_project_donation_list_co_financing_is_unspecified(self, check_status_psp):
        # Co_financing order and donation
        order = OrderFactory.create(user=self.user2, status=StatusDefinition.SUCCESS)
        DonationFactory.create(amount=1500, project=self.project3,
                               order=order)

        # Anonymous order and donation
        anonymous_order = OrderFactory.create(status=StatusDefinition.SUCCESS)
        DonationFactory.create(amount=1500, project=self.project3,
                               order=anonymous_order, anonymous=True)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2,
                         'Donations and anonymous donations should be returned')
        self.assertEqual(response.data['results'][0]['amount']['amount'], 1500.00)
        self.assertEqual(response.data['results'][1]['amount']['amount'], 1000.00)


@patch.object(ManageOrderDetail, 'check_status_psp')
class TestMyProjectDonationList(DonationApiTestCase):
    """
    Test that the project donations list only works for the project owner
    """

    def setUp(self):
        super(TestMyProjectDonationList, self).setUp()

        self.project3 = ProjectFactory.create(amount_asked=5000,
                                              owner=self.user1)
        self.project3.set_status('campaign')

        # User 2 makes a donation
        order = OrderFactory.create(user=self.user2)
        DonationFactory.create(amount=1000, project=self.project3,
                               order=order)
        order.locked()
        order.save()
        order.success()
        order.save()

        self.project_donation_list_url = reverse('my-project-donation-list')

    def tearDown(self):
        super(TestMyProjectDonationList, self).tearDown()
        # Order.objects.delete()

    def test_my_project_donation_list(self, check_status_psp):
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        donation = response.data['results'][0]
        self.assertEqual(donation['amount']['amount'], 1000.00)
        self.assertEqual(donation['project'], self.project3.id)

    def test_successful_my_project_donation_list(self, check_status_psp):
        # Unsuccessful donations should not be shown
        order = OrderFactory.create(user=self.user2)
        DonationFactory.create(amount=2000, project=self.project3,
                               order=order)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1,
                         'Only the successful donation should be returned')

    def test_my_project_donation_list_unauthorized(self, check_status_psp):
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@patch.object(ManageOrderDetail, 'check_status_psp')
class TestMyFundraiserDonationList(DonationApiTestCase):
    """
    Test that the fundraiser donations list only works for the fundraiser owner
    """

    def setUp(self):
        super(TestMyFundraiserDonationList, self).setUp()

        self.project4 = ProjectFactory.create(amount_asked=5000,
                                              owner=self.user1)
        self.project4.set_status('campaign')
        self.fundraiser = FundraiserFactory.create(amount=4000,
                                                   owner=self.user1,
                                                   project=self.project4)

        # User 2 makes a donation
        order = OrderFactory.create(user=self.user2)
        DonationFactory.create(amount=1000, project=self.project4,
                               fundraiser=self.fundraiser,
                               order=order)

        order.locked()
        order.save()
        order.success()
        order.save()

        self.fundraiser_donation_list_url = reverse(
            'my-fundraiser-donation-list')

    def test_my_fundraiser_donation_list(self, check_status_psp):
        response = self.client.get(self.fundraiser_donation_list_url,
                                   {'fundraiser': self.fundraiser.pk},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        donation = response.data[0]

        self.assertEqual(donation['amount']['amount'], 1000.00)
        self.assertEqual(donation['project'], self.project4.id)
        self.assertEqual(donation['fundraiser'], self.fundraiser.pk)

    def test_successful_my_fundraiser_donation_list(self, check_status_psp):
        # Unsuccessful donations should not be shown
        order = OrderFactory.create(user=self.user2)
        DonationFactory.create(amount=2000, project=self.project4,
                               fundraiser=self.fundraiser,
                               order=order)

        response = self.client.get(self.fundraiser_donation_list_url,
                                   {'fundraiser': self.fundraiser.pk},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1,
                         'Only the successful donation should be returned')

    def test_my_fundraiser_donation_list_unauthorized(self, check_status_psp):
        response = self.client.get(self.fundraiser_donation_list_url,
                                   {'project': self.fundraiser.pk},
                                   token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestLatestDonationListApi(DonationApiTestCase):
    """
    Test that the fundraiser donations list only works for the fundraiser owner
    """

    def setUp(self):
        super(TestLatestDonationListApi, self).setUp()
        self.user2.is_staff = True
        self.user2.save()

        self.project = ProjectFactory.create(amount_asked=5000,
                                             owner=self.user1)

        self.project.set_status('campaign')

        # User 2 makes a donation
        order = OrderFactory.create(user=self.user2)
        DonationFactory.create(amount=1000, project=self.project,
                               order=order)

        order.locked()
        order.save()
        order.success()
        order.save()

    def test_donation_list(self):
        response = self.client.get('/api/donations/latest-donations/',
                                   token=self.user2_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestDonationSettingsApi(DonationApiTestCase):
    """
    Test that donation settings are reflected in the API
    - Test that donation amount is shown or hidden
    - Test donation settings are shown in config api
    """

    def setUp(self):
        super(TestDonationSettingsApi, self).setUp()
        self.project = ProjectFactory.create(amount_asked=5000)
        self.project.set_status('campaign')
        self.user = BlueBottleUserFactory.create()

        order = OrderFactory.create()
        DonationFactory.create(amount=1000, project=self.project, order=order)
        order.locked()
        order.save()
        order.success()
        order.save()
        self.project_donation_list_url = reverse('project-donation-list')
        self.settings_url = reverse('settings')

    def test_donation_settings(self):
        donation_settings = DonationPlatformSettings.load()
        amounts = DonationDefaultAmounts.objects.first()
        amounts.value1 = 10
        amounts.value2 = 11
        amounts.value3 = 12
        amounts.value4 = 13
        amounts.save()

        donation_settings.show_donation_amount = False
        donation_settings.save()

        response = self.client.get(self.settings_url, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['platform']['donations']['default_amounts'][0]['amounts'],
            [10, 11, 12, 13]
        )

    def test_donation_amount_not_shown(self):
        donation_settings = DonationPlatformSettings.load()
        donation_settings.show_donation_amount = False
        donation_settings.save()
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project.slug},
                                   token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse('amount' in response.data['results'][0])

    def test_donation_amount_shown(self):
        donation_settings = DonationPlatformSettings.load()
        donation_settings.show_donation_amount = True
        donation_settings.save()
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project.slug},
                                   token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('amount' in response.data['results'][0])
