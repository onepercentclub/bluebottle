from django.test import RequestFactory
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

        self.not_owner = BlueBottleUserFactory.create()
        self.not_owner_token = "JWT {0}".format(self.not_owner.get_jwt_token())
        self.project = ProjectFactory.create(owner=self.owner)
        RewardFactory.create(project=self.project)
        RewardFactory.create(project=self.project)

        self.project_manage_url = reverse(
            'project_manage_detail', kwargs={'slug': self.project.slug}
        )

        self.project_detail_url = reverse(
            'project_detail', kwargs={'slug': self.project.slug}
        )

    def test_manage_owner_permissions(self):
        # view allowed
        response = self.client.get(self.project_manage_url, token=self.owner_token)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data['permissions']['GET'], True
        )
        self.assertEqual(
            response.data['permissions']['PUT'], True
        )

        self.assertEqual(
            response.data['related_permissions']['rewards']['GET'], True
        )

        self.assertEqual(
            response.data['related_permissions']['rewards']['POST'], True
        )

    def test_manage_non_owner_permissions(self):
        # view allowed
        response = self.client.get(self.project_manage_url, token=self.not_owner_token)
        self.assertEqual(response.status_code, 403)

    def test_owner_permissions(self):
        # view allowed
        response = self.client.get(self.project_detail_url, token=self.owner_token)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data['permissions']['GET'], True
        )

        self.assertEqual(
            response.data['related_permissions']['rewards']['GET'], True
        )

        self.assertEqual(
            response.data['related_permissions']['rewards']['POST'], True
        )

    def test_non_owner_permissions(self):
        # view allowed
        response = self.client.get(self.project_detail_url, token=self.not_owner_token)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data['permissions']['GET'], True
        )

        self.assertEqual(
            response.data['related_permissions']['rewards']['GET'], True
        )

        self.assertEqual(
            response.data['related_permissions']['rewards']['POST'], False
        )
