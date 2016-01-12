from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.rewards import RewardFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.utils.utils import StatusDefinition


class RewardTestCase(BluebottleTestCase):
    """
    Test Reward API endpoints
    """

    def setUp(self):
        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        campaign_phase = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(status=campaign_phase, owner=self.user)
        self.project2 = ProjectFactory.create(status=campaign_phase)

        self.project_reward_url = reverse('project-reward-list',
                                          kwargs={'project_slug': self.project.slug})

        self.reward_data = {
            'project': self.project.slug,
            'title': 'Free goodies',
            'description': 'Free bag of goodies'
        }

    def test_reward_list(self):
        RewardFactory.create(project=self.project)

        response = self.client.get(self.project_reward_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_reward_list_should_only_show_given_project(self):
        RewardFactory.create_batch(4, project=self.project)
        RewardFactory.create_batch(3, project=self.project2)

        response = self.client.get(self.project_reward_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)

    def test_reward_can_be_created_by_project_owner(self):
        response = self.client.post(self.project_reward_url,
                                    self.reward_data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], self.reward_data['title'])

    def test_reward_can_not_be_created_by_non_project_owner(self):
        response = self.client.post(self.project_reward_url,
                                    self.reward_data,
                                    token=self.user_token)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], self.reward_data['title'])

    def test_reward_can_be_deleted(self):
        self.assertTrue(False)

    def test_reward_with_donations_can_not_be_deleted(self):
        self.assertTrue(False)

    def test_reward_can_only_be_deleted_by_project_owner(self):
        self.assertTrue(False)


