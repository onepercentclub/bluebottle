from django.test import RequestFactory
from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.rewards import RewardFactory
from bluebottle.test.utils import BluebottleTestCase


# RequestFactory used for integration tests.
factory = RequestFactory()


class ProjectPermissionsTestCase(BluebottleTestCase):
    """
    Tests for the Project API permissions.
    """
    def setUp(self):
        super(ProjectPermissionsTestCase, self).setUp()
        self.init_projects()

        self.owner = BlueBottleUserFactory.create()
        self.owner_token = "JWT {0}".format(self.owner.get_jwt_token())

        self.owner.user_permissions.add(
            Permission.objects.get(codename='api_add_reward')
        )

        self.not_owner = BlueBottleUserFactory.create()
        self.not_owner_token = "JWT {0}".format(self.not_owner.get_jwt_token())
        self.project = ProjectFactory.create(owner=self.owner)
        RewardFactory.create(project=self.project)
        RewardFactory.create(project=self.project)

        self.project_manage_url = reverse(
            'project_manage_detail', kwargs={'slug': self.project.slug})
        self.project_manage_list_url = reverse('project_manage_list')

    def test_owner_permissions(self):
        # view allowed
        response = self.client.get(self.project_manage_url, token=self.owner_token)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data['permissions']['GET'], True
        )
        self.assertEqual(
            response.data['related_permissions']['rewards']['GET'], True
        )
