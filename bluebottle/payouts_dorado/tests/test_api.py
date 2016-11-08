from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.utils.timezone import now

from rest_framework import status

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.payouts import ProjectPayoutFactory
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
