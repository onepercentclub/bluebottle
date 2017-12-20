from django.test import RequestFactory
from django.contrib.auth.models import Group, Permission
from django.core.urlresolvers import reverse

from bluebottle.bb_projects.models import ProjectPhase
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

        self.assertEqual(
            response.data['related_permissions']['donations']['GET'], True
        )
        self.assertEqual(
            response.data['related_permissions']['donations']['POST'], True
        )

    def test_manage_owner_running_permissions(self):
        # view allowed
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        response = self.client.get(self.project_manage_url, token=self.owner_token)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data['permissions']['GET'], True
        )
        self.assertEqual(
            response.data['permissions']['PUT'], False
        )

    def test_manage_owner_running_permissions_with_permission(self):
        # view allowed
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.add(
            Permission.objects.get(codename='api_change_own_running_project')
        )

        response = self.client.get(self.project_manage_url, token=self.owner_token)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data['permissions']['GET'], True
        )
        self.assertEqual(
            response.data['permissions']['PUT'], True
        )

    def test_manage_non_owner_permissions(self):
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        response = self.client.put(self.project_manage_url, token=self.not_owner_token)
        self.assertEqual(response.status_code, 403)

    def test_manage_non_owner_permissions_running_has_permission(self):
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.add(
            Permission.objects.get(codename='api_change_own_running_project')
        )

        response = self.client.put(self.project_manage_url, token=self.not_owner_token)
        self.assertEqual(response.status_code, 403)

    def test_manage_non_owner_permissions_running(self):
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

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

        self.assertEqual(
            response.data['related_permissions']['manage_project']['PUT'], True
        )

    def test_owner_permissions_running(self):
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

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

        self.assertEqual(
            response.data['related_permissions']['manage_project']['PUT'], False
        )

    def test_owner_edit_permissions(self):
        self.project.status = ProjectPhase.objects.get(slug='campaign')
        self.project.save()

        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.add(
            Permission.objects.get(codename='api_change_own_running_project')
        )

        # view allowed
        response = self.client.get(self.project_detail_url, token=self.owner_token)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data['permissions']['GET'], True
        )

        self.assertEqual(
            response.data['related_permissions']['manage_project']['PUT'], True
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

    def test_anonymous_permissions(self):
        # view allowed
        response = self.client.get(self.project_detail_url)
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

        self.assertEqual(
            response.data['related_permissions']['donations']['GET'], False
        )
        self.assertEqual(
            response.data['related_permissions']['donations']['POST'], True
        )
