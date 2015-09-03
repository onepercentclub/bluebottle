from mock import patch

from bluebottle.test.utils import BluebottleTestCase
from django.conf import settings

from bluebottle.bb_orders.views import ManageOrderDetail
from django.core.urlresolvers import reverse
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.utils.model_dispatcher import get_order_model, get_model_class
from bluebottle.test.factory_models.fundraisers import FundraiserFactory

from django.utils.importlib import import_module

from bluebottle.utils.utils import StatusDefinition

from rest_framework import status

ORDER_MODEL = get_order_model()
DONATION_MODEL = get_model_class("DONATIONS_DONATION_MODEL")


class DonationApiTestCase(BluebottleTestCase):
    def setUp(self):
        super(DonationApiTestCase, self).setUp()

        settings.SESSION_ENGINE = 'django.contrib.sessions.backends.file'
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore()
        store.save()
        self.session = store
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key

        self.addCleanup(self._clear_session)

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.init_projects()

        self.project1 = ProjectFactory.create(amount_asked=5000)
        self.project1.set_status('campaign')

        self.project2 = ProjectFactory.create(amount_asked=3750)
        self.project2.set_status('campaign')

        self.manage_order_list_url = reverse('manage-order-list')
        self.manage_donation_list_url = reverse('manage-donation-list')

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create(user_type='company')
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.project = ProjectFactory.create()
        self.order = OrderFactory.create(user=self.user)

    def _clear_session(self):
        self.session.flush()


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

        self.assertEqual(DONATION_MODEL.objects.count(), 0)
        response = self.client.post(reverse('manage-donation-list'), donation1,
                                    token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DONATION_MODEL.objects.count(), 1)

    def test_user_is_not_order_owner(self, mock_check_status_psp):
        """ Test that a user who is not owner of an order cannot create a new donation """

        donation1 = {
            "project": self.project.slug,
            "order": self.order.id,
            "amount": 35
        }

        self.assertEqual(DONATION_MODEL.objects.count(), 0)
        response = self.client.post(reverse('manage-donation-list'), donation1,
                                    token=self.user2_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(DONATION_MODEL.objects.count(), 0)

    def test_order_status_not_new(self, mock_check_status_psp):
        """ Test that a non-new order status produces a forbidden response """

        order = OrderFactory.create(user=self.user,
                                    status=StatusDefinition.SUCCESS)

        donation1 = {
            "project": self.project.slug,
            "order": order.id,
            "amount": 35
        }

        self.assertEqual(DONATION_MODEL.objects.count(), 0)
        response = self.client.post(reverse('manage-donation-list'), donation1,
                                    token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(DONATION_MODEL.objects.count(), 0)

    def test_order_status_new(self, mock_check_status_psp):
        """ Test that a new order status produces a 201 created response """

        order = OrderFactory.create(user=self.user,
                                    status=StatusDefinition.CREATED)

        donation1 = {
            "project": self.project.slug,
            "order": order.id,
            "amount": 35
        }

        self.assertEqual(DONATION_MODEL.objects.count(), 0)
        response = self.client.post(reverse('manage-donation-list'), donation1,
                                    token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DONATION_MODEL.objects.count(), 1)

    def test_donation_update_not_same_owner(self, mock_check_status_psp):
        """ Test that an update to a donation where the user is not the owner produces a 403"""

        donation = DonationFactory(order=self.order, amount=35)

        updated_donation = {
            "project": self.project.slug,
            "order": self.order.id,
            "amount": 50
        }

        self.assertEqual(DONATION_MODEL.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user2_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(DONATION_MODEL.objects.count(), 1)

    def test_donation_update_same_owner(self, mock_check_status_psp):
        """ Test that an update to a donation where the user is the owner produces a 200 OK"""

        donation = DonationFactory(order=self.order, amount=35)

        updated_donation = {
            "project": self.project.slug,
            "order": self.order.id,
            "amount": 50
        }

        self.assertEqual(DONATION_MODEL.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DONATION_MODEL.objects.count(), 1)

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

        self.assertEqual(DONATION_MODEL.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(DONATION_MODEL.objects.count(), 1)

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

        self.assertEqual(DONATION_MODEL.objects.count(), 1)
        response = self.client.put(reverse('manage-donation-detail',
                                           kwargs={'pk': donation.id}),
                                   updated_donation,
                                   token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(DONATION_MODEL.objects.count(), 1)


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
        response.data['id']

        # Check that the order total is equal to the donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 50)

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
        response.data['id']

        # Check that the order total is equal to the donation amount
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 35)

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
        self.assertEqual(response.data['total'], 35)

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
        self.assertEqual(response.data['total'], 50)

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
        self.assertEqual(response.data['total'], 97)

        # remove the first donation
        response = self.client.delete(donation_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Check that the order total is equal to second donation
        order_url = "{0}{1}".format(self.manage_order_list_url, order_id)
        response = self.client.get(order_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['donations']), 1)
        self.assertEqual(response.data['total'], 47)

        # Set order to status 'locked'
        order = ORDER_MODEL.objects.get(id=order_id)
        order.locked()

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


class TestAnonymousAuthenicatedDonationCreate(DonationApiTestCase):
    def test_create_anonymous_donation(self):
        donation_url = reverse('manage-donation-list')

        # create a new anonymous donation
        response = self.client.post(donation_url, {'order': self.order.pk,
                                                   'project': self.project.slug,
                                                   'amount': 50,
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
        self.order.succeeded()

        # retrieve the donation through public API
        donation_url = reverse('donation-detail', kwargs={'pk': donation_id})
        response = self.client.get(donation_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that user is NOT shown in public API
        self.assertEqual(None, response.data['user'])


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
        DonationFactory.create(amount=1000, project=self.project3,
                               order=order)

        self.project_donation_list_url = reverse('project-donation-list')

    def test_project_donation_list(self, check_status_psp):
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

        donation = response.data['results'][0]
        self.assertEqual(donation['amount'], 1000.0)
        self.assertEqual(donation['project'], self.project3.pk)

    def test_successful_project_donation_list(self, check_status_psp):
        # Unsuccessful donations should not be shown
        order = OrderFactory.create(user=self.user2)
        DonationFactory.create(amount=2000, project=self.project3,
                               order=order)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1,
                         'Only the successful donation should be returned')

    def test_successful_project_donation_list_paged(self, check_status_psp):
        for i in range(30):
            order = OrderFactory.create(user=self.user2, status=StatusDefinition.SUCCESS)
            DonationFactory.create(amount=2000, project=self.project3,
                                   order=order)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 31,
                         'Only the successful donation should be returned')
        self.assertEqual(len(response.data['results']), 20)

    def test_project_donation_list_co_financing(self, check_status_psp):
        order = OrderFactory.create(user=self.user2, status=StatusDefinition.SUCCESS)
        DonationFactory.create(amount=1000, project=self.project3,
                               order=order)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug, 'co_financing': None},
                                   token=self.user1_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1,
                         'Only donations by companies should be returned')


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
        order.succeeded()

        self.project_donation_list_url = reverse('my-project-donation-list')

    def test_my_project_donation_list(self, check_status_psp):
        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        donation = response.data[0]
        self.assertEqual(donation['amount'], 1000.0)
        self.assertEqual(donation['project'], self.project3.pk)

    def test_successful_my_project_donation_list(self, check_status_psp):
        # Unsuccessful donations should not be shown
        order = OrderFactory.create(user=self.user2)
        DonationFactory.create(amount=2000, project=self.project3,
                               order=order)

        response = self.client.get(self.project_donation_list_url,
                                   {'project': self.project3.slug},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1,
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
        order.succeeded()

        self.fundraiser_donation_list_url = reverse(
            'my-fundraiser-donation-list')

    def test_my_fundraiser_donation_list(self, check_status_psp):
        response = self.client.get(self.fundraiser_donation_list_url,
                                   {'fundraiser': self.fundraiser.pk},
                                   token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        donation = response.data[0]
        self.assertEqual(donation['amount'], 1000.0)
        self.assertEqual(donation['project'], self.project4.pk)
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
