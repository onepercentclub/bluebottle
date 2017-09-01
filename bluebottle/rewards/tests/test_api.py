from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.rewards import RewardFactory
from bluebottle.test.utils import BluebottleTestCase


class RewardTestCase(BluebottleTestCase):
    """
    Test Reward API endpoints
    """

    def setUp(self):
        super(RewardTestCase, self).setUp()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.user2 = BlueBottleUserFactory.create()
        self.user2_token = "JWT {0}".format(self.user2.get_jwt_token())

        self.init_projects()

        campaign_phase = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(status=campaign_phase, owner=self.user)
        self.project2 = ProjectFactory.create(status=campaign_phase)

        self.reward_url = reverse('reward-list')

        self.reward_data = {
            'project': self.project.slug,
            'title': 'Free goodies',
            'amount': '20.00',
            'limit': 0,
            'description': 'Free bag of goodies'
        }

    def test_reward_list(self):
        """
        Test getting a list of rewards for a project.
        """
        RewardFactory.create_batch(4, project=self.project)

        response = self.client.get(self.reward_url, {'project': self.project.slug})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)

    def test_reward_list_should_only_show_given_project(self):
        """
        Make sure only rewards for the given project are shown.
        """
        RewardFactory.create_batch(4, project=self.project)
        RewardFactory.create_batch(3, project=self.project2)
        response = self.client.get(self.reward_url, {'project': self.project.slug})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)

    def test_reward_list_only_own_projects(self):
        """
        Make sure only rewards for the given project are shown.
        """
        RewardFactory.create(project=self.project)
        RewardFactory.create(project=self.project)
        RewardFactory.create(project=self.project2)

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_reward')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_reward')
        )

        response = self.client.get(
            self.reward_url,
            token=self.user_token
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_reward_can_be_created_by_project_owner(self):
        """
        Project owner should be able to create a new reward for that project.
        """
        response = self.client.post(self.reward_url,
                                    self.reward_data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], self.reward_data['title'])

    def test_reward_cannot_have_an_amount_below_5(self):
        """
        Rewards have a minimum amount
        """

        response = self.client.post(self.reward_url,
                                    dict(self.reward_data, amount=1),
                                    token=self.user_token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data['amount'], [u'Ensure this amount is greater than or equal to 5.0.']
        )

    def test_reward_can_not_be_created_by_non_project_owner(self):
        """
        Non-project owner should not be allowed to create
        a reward for that project.
        """
        response = self.client.post(self.reward_url,
                                    self.reward_data,
                                    token=self.user2_token)
        self.assertEqual(response.status_code, 403)

    def test_reward_cannot_have_different_currency_from_project(self):
        """
        Rewards have a minimum amount
        """
        amount = {'currency': 'USD', 'amount': 100}

        response = self.client.post(self.reward_url,
                                    dict(self.reward_data, amount=amount),
                                    token=self.user_token)
        self.assertEqual(response.status_code, 400)

        self.assertEqual(
            unicode(response.data['non_field_errors'][0]),
            u'Currency does not match project any of the currencies.'
        )

    def test_reward_can_be_deleted(self):
        """
        Project owner can delete a reward on a project.
        """
        reward = RewardFactory.create(project=self.project)
        reward_url = reverse('reward-detail', kwargs={'pk': reward.id})
        response = self.client.delete(reward_url, token=self.user_token)
        self.assertEqual(response.status_code, 204)

    def test_reward_with_donations_can_not_be_deleted(self):
        """
        Project owner can't delete a reward which has donations.
        """
        reward = RewardFactory.create(project=self.project)
        reward_url = reverse('reward-detail', kwargs={'pk': reward.id})
        donation = DonationFactory.create(reward=reward, project=self.project)
        donation.order.locked()
        donation.order.save()
        donation.order.success()
        donation.order.save()
        donation.save()
        response = self.client.delete(reward_url, token=self.user_token)
        self.assertEqual(response.status_code, 403)

    def test_reward_can_only_be_deleted_by_project_owner(self):
        """
        Non project owner can't delete a reward on that project.
        """
        reward = RewardFactory.create(project=self.project)
        reward_url = reverse('reward-detail', kwargs={'pk': reward.id})
        response = self.client.delete(reward_url, token=self.user2_token)
        self.assertEqual(response.status_code, 403)
