from django.core.urlresolvers import reverse

from rest_framework import status
from bluebottle.test.utils import BluebottleTestCase


class RewardTestCase(BluebottleTestCase):
    """
    Test Reward API endpoints
    """

    def test_reward_list(self):
        """
        Ensure get request returns 200.
        """
        response = self.client.get(reverse('project-reward-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)


    def test_reward_list_should_only_show_given_project(self):
        self.assertTrue(False)

    def test_reward_can_be_created_by_project_owner(self):
        self.assertTrue(False)

    def test_reward_can_not_be_created_by_non_project_owner(self):
        self.assertTrue(False)

    def test_reward_can_be_deleted(self):
        self.assertTrue(False)

    def test_reward_with_donations_can_not_be_deleted(self):
        self.assertTrue(False)

    def test_reward_can_only_be_deleted_by_project_owner(self):
        self.assertTrue(False)


