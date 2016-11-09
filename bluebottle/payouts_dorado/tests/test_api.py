from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.timezone import now

from rest_framework import status

from bluebottle.payouts_dorado.models import Payout
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


class TestPayoutApi(BluebottleTestCase):
    """
    Test Payouts API
    """

    def setUp(self):
        super(TestPayoutApi, self).setUp()
        self.init_projects()

        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())
        financial = Group.objects.get(name='Financial')
        financial.user_set.add(self.user2)

        self.project = ProjectFactory.create(campaign_ended=now())

        self.payout_url = reverse('project-payout-detail', kwargs={'pk': self.project.id})

    def test_payouts_api_access_denied_for_anonymous(self):
        """
        """
        response = self.client.get(self.payout_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payouts_api_access_denied_for_normal_user(self):
        """
        """
        response = self.client.get(self.payout_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payouts_api_access_granted_for_power_user(self):
        """
        """
        response = self.client.get(self.payout_url, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestPayoutMethodApi(BluebottleTestCase):
    """
    Test Payout Methods API
    """

    def setUp(self):
        super(TestPayoutMethodApi, self).setUp()
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())
        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())
        financial = Group.objects.get(name='Financial')
        financial.user_set.add(self.user2)
        self.payoutmethods_url = reverse('payout-method-list')

    def test_payoutmethods_api_access_denied_for_anonymous(self):
        """
        """
        response = self.client.get(self.payoutmethods_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_payoutmethods_api_access_denied_for_normal_user(self):
        """
        """
        response = self.client.get(self.payoutmethods_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payoutmethods_api_access_granted_for_power_user(self):
        """
        """
        response = self.client.get(self.payoutmethods_url, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['method'], 'duckbank')


class TestPayoutUpdateApi(BluebottleTestCase):
    """
    Test Payout Update API
    """

    def setUp(self):
        super(TestPayoutUpdateApi, self).setUp()
        self.init_projects()
        self.user1 = BlueBottleUserFactory.create()
        self.user1_token = "JWT {0}".format(self.user1.get_jwt_token())
        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())
        financial = Group.objects.get(name='Financial')
        financial.user_set.add(self.user2)
        self.payout_url = reverse('payout-detail')
        self.project = ProjectFactory.create(campaign_ended=now())

    def test_payout_update_api_access_denied_for_normal_user(self):
        """
        Normal users should not be allowed to post to payout update url
        """
        response = self.client.get(self.payout_url, token=self.user1_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_payout_update_api_access_granted_for_power_user(self):
        """
        Post/put to payout update url should create or update it
        """
        data = {
            'id': 'onepercent-123456',
            'project_id': self.project.id,
            'amount': {'amount': 570, 'currency': 'EUR'},
            'status': 'in_progress'
        }
        response = self.client.put(self.payout_url, data, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['remote_id'], 'onepercent-123456')
        self.assertEqual(response.data['status'], 'in_progress')

        data = {
            'id': 'onepercent-123456',
            'project_id': self.project.id,
            'amount': {'amount': 570, 'currency': 'EUR'},
            'status': 'settled'
        }
        response = self.client.put(self.payout_url, data, token=self.user2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['remote_id'], 'onepercent-123456')
        self.assertEqual(response.data['status'], 'settled')

        # Because we have updated the previous one we should only have 1 payout
        self.assertEqual(Payout.objects.count(), 1)
