from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.members.models import MemberPlatformSettings
from bluebottle.tasks.models import Task, TaskMember
from bluebottle.projects.models import Project
from bluebottle.donations.models import Donation
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.tasks import TaskMemberFactory, TaskFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.utils import BluebottleTestCase


class ProjectPlatformSettingsTestCase(BluebottleTestCase):
    """
    Integration tests for the ProjectPlatformSettings API.
    """
    def test_member_platform_settings(self):
        MemberPlatformSettings.objects.create(
            require_consent=True,
            consent_link='http://example.com'
        )

        response = self.client.get(reverse('settings'))
        self.assertEqual(response.data['platform']['members']['require_consent'], True)
        self.assertEqual(
            response.data['platform']['members']['consent_link'],
            'http://example.com'
        )

    def test_member_platform_settings_default(self):
        response = self.client.get(reverse('settings'))
        self.assertEqual(response.data['platform']['members']['require_consent'], False)
        self.assertEqual(
            response.data['platform']['members']['consent_link'],
            '/pages/terms-and-conditions'
        )


class UserDataExportTest(BluebottleTestCase):
    """
    Integration tests for the User API.
    """

    def setUp(self):
        super(UserDataExportTest, self).setUp()

        self.user_1 = BlueBottleUserFactory.create()
        self.user_1_token = "JWT {0}".format(self.user_1.get_jwt_token())

        self.user_2 = BlueBottleUserFactory.create()
        self.user_2_token = "JWT {0}".format(self.user_2.get_jwt_token())

        for i in range(0, 10):
            ProjectFactory.create(owner=self.user_1)
            TaskFactory.create(author=self.user_1)
            TaskMemberFactory.create(member=self.user_1)
            order = OrderFactory.create(user=self.user_1)
            DonationFactory.create(order=order)

        # User with partner organization
        self.user_export_url = reverse('user-export')

    def test_current_user(self):
        """
        Test retrieving the currently logged in user after login.
        """
        response = self.client.get(self.user_export_url, token=self.user_1_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['first_name'], self.user_1.first_name)
        self.assertEqual(response.data['last_name'], self.user_1.first_name)

        self.assertEqual(len(response.data['projects']), 10)
        project_ids = [project.slug for project in Project.objects.filter(owner=self.user_1)]
        for project in response.data['projects']:
            self.assertTrue(project['id'] in project_ids)

        self.assertEqual(len(response.data['tasks']), 10)
        task_ids = [task.pk for task in Task.objects.filter(author=self.user_1)]
        for task in response.data['tasks']:
            self.assertTrue(task['id'] in task_ids)

        self.assertEqual(len(response.data['task_members']), 10)
        task_member_ids = [task.pk for task in TaskMember.objects.filter(member=self.user_1)]
        for task_member in response.data['task_members']:
            self.assertTrue(task_member['id'] in task_member_ids)

        self.assertEqual(len(response.data['donations']), 10)
        donation_ids = [donation.pk for donation in Donation.objects.filter(order__user=self.user_1)]
        for donation in response.data['donations']:
            self.assertTrue(donation['id'] in donation_ids)

    def test_user_2_(self):
        """
        Test retrieving the currently logged in user after login.
        """
        response = self.client.get(self.user_export_url, token=self.user_2_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], self.user_2.first_name)
        self.assertEqual(response.data['last_name'], self.user_2.first_name)
        self.assertEqual(len(response.data['projects']), 0)
        self.assertEqual(len(response.data['donations']), 0)
        self.assertEqual(len(response.data['tasks']), 0)
        self.assertEqual(len(response.data['task_members']), 0)

    def test_unauthenticated(self):
        response = self.client.get(self.user_export_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
