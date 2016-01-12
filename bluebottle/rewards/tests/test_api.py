from django.core.urlresolvers import reverse

from rest_framework import status
from bluebottle.test.utils import BluebottleTestCase


class RewardTestCase(BluebottleTestCase):
    """
    Test Reward API endpoints
    """

    def test_api_reward_list(self):
        """
        Ensure get request returns 200.
        """
        response = self.client.get(reverse('project-reward-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

