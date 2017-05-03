import mock

from django.core.urlresolvers import reverse

from rest_framework import status

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.models import Task
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory


class TaskApiTestcase(BluebottleTestCase):
    """ Tests tasks api """

    def setUp(self):
        super(TaskApiTestcase, self).setUp()

        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        campaign_status = ProjectPhase.objects.get(slug='campaign')
        self.some_project = ProjectFactory.create(owner=self.some_user,
                                                  status=campaign_status)

        self.task1 = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_project.owner,
            project=self.some_project,
            people_needed=2
        )

        self.another_user = BlueBottleUserFactory.create()
        self.another_token = "JWT {0}".format(self.another_user.get_jwt_token())

        self.yet_another_user = BlueBottleUserFactory.create()
        self.yet_another_token = "JWT {0}".format(
            self.yet_another_user.get_jwt_token())

        self.previews_url = reverse('project_preview_list')
        self.task_preview_url = reverse('task_preview_list')
        self.tasks_url = reverse('task_list')
        self.task_member_url = reverse('task_member_list')

    def test_task_count(self):
        """
        Test various task_count values
        """

        # No task members assigned to a task of a project, so there is a task open
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 1)

        TaskMemberFactory.create(member=self.another_user,
                                 task=self.task1,
                                 status='accepted')

        # The task has one task member and two people needed, still one task open
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 1)

        task_member2 = TaskMemberFactory.create(member=self.yet_another_user,
                                                task=self.task1,
                                                status='accepted')

        # The task has two accepted task members for two people_needed, no more task open
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 0)

        task_member2.status = 'applied'
        task_member2.save()

        # FIXME: Make sure task is marked as available in the code.
        # The task has one accepted task member and one applied member, still one open task
        # response = self.client.get(self.previews_url, HTTP_AUTHORIZATION=self.some_token)
        # self.assertEqual(response.data['results'][0]['task_count'], 1)

        self.task1.status = Task.TaskStatuses.closed
        self.task1.save()

        # The task is closed, so don't give a task_count
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 0)

        self.task1.status = Task.TaskStatuses.realized
        self.task1.save()

        # The task is realized, so don't give a task_count
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 0)

        self.task1.status = Task.TaskStatuses.open
        self.task1.save()

        TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_project.owner,
            project=self.some_project,
            people_needed=2
        )

        # There are now two tasks for the same project, so task_count gives 2
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 2)

    def test_status_task_preview_response(self):
        """ Test retrieval of task previews with correct status."""
        self.status_response(self.task_preview_url)

    def test_status_task_response(self):
        """ Test retrieval of tasks with correct status."""
        self.status_response(self.tasks_url)

    def status_response(self, url):
        self.task1.delete()

        task1 = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_project.owner,
            project=self.some_project,
            people_needed=2
        )

        task2 = TaskFactory.create(
            status=Task.TaskStatuses.closed,
            author=self.some_project.owner,
            project=self.some_project,
            people_needed=2
        )

        task3 = TaskFactory.create(
            status=Task.TaskStatuses.realized,
            author=self.some_project.owner,
            project=self.some_project,
            people_needed=2
        )

        task4 = TaskFactory.create(
            status=Task.TaskStatuses.in_progress,
            author=self.some_project.owner,
            project=self.some_project,
            people_needed=2
        )

        response = self.client.get(url,
                                   {'status': 'open'},
                                   HTTP_AUTHORIZATION=self.some_token)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], task1.id)

        response = self.client.get(url,
                                   {'status': 'closed'},
                                   HTTP_AUTHORIZATION=self.some_token)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], task2.id)

        response = self.client.get(url,
                                   {'status': 'realized'},
                                   HTTP_AUTHORIZATION=self.some_token)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], task3.id)

        response = self.client.get(url,
                                   {'status': 'in progress'},
                                   HTTP_AUTHORIZATION=self.some_token)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], task4.id)

    def test_task_status_changes(self):
        task = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.some_project,
            people_needed=1
        )

        task_url = reverse('task_detail', kwargs={'pk': task.id})
        task_member_data = {
            'task': task.id,
            'motivation': 'Pick me!'
        }

        # Task should have status 'open' at first.
        response = self.client.get(task_url)
        self.assertEqual(response.data['status'], 'open')

        # When a member applies and is accepted task status should change to 'in progress'
        response = self.client.post(self.task_member_url,
                                    task_member_data,
                                    HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_member_id = response.data['id']
        task_member_url = reverse('task_member_detail', kwargs={'pk': task_member_id})
        response = self.client.patch(task_member_url,
                                     {'status': 'accepted'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(task_url)
        self.assertEqual(response.data['status'], 'in progress')

        # When the accepted member is rejected task status should change back to 'open'
        response = self.client.patch(task_member_url,
                                     {'status': 'rejected'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(task_url)
        self.assertEqual(response.data['status'], 'open')

        # When a member is accepted task status should change to 'in progress'
        response = self.client.post(self.task_member_url,
                                    task_member_data,
                                    HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_member_id = response.data['id']
        task_member_url = reverse('task_member_detail', kwargs={'pk': task_member_id})
        response = self.client.patch(task_member_url,
                                     {'status': 'accepted'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(task_url)
        self.assertEqual(response.data['status'], 'in progress')

        # When a applied member is withdraws task status should change to 'open'
        response = self.client.put(task_member_url,
                                   {
                                       'status': 'withdrew',
                                       'task': task.id
                                   },
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(task_url)
        self.assertEqual(response.data['status'], 'open')

        # When a member is accepted task status should change to 'in progress'
        response = self.client.post(self.task_member_url,
                                    task_member_data,
                                    HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_member_id = response.data['id']
        task_member_url = reverse('task_member_detail', kwargs={'pk': task_member_id})
        response = self.client.patch(task_member_url,
                                     {'status': 'accepted'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(task_url)
        self.assertEqual(response.data['status'], 'in progress')

        # When a applied member is realized task status should stay 'in progress''
        response = self.client.patch(task_member_url,
                                     {'status': 'realized'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(task_url)
        self.assertEqual(response.data['status'], 'in progress')

    def test_deadline_dates(self):
        """
        Test the setting of the deadline of a Task on save to the end of a day.
        """
        task_data = {
            'people_needed': 1,
            'deadline': '2016-08-09T12:45:14.134756',
            'deadline_to_apply': '2016-08-04T12:45:14.134756',
            'project': self.some_project.slug,
            'title': 'Help me',
            'description': 'I need help',
            'location': '',
            'skill': 1,
            'time_needed': '4.00',
            'type': 'event'
        }

        # Task deadline time should changed be just before midnight after setting.
        response = self.client.post(self.tasks_url, task_data,
                                    HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['deadline'], '2016-08-09T23:59:59.999999+02:00')


class TestProjectTaskAPIPermissions(BluebottleTestCase):
    """ API endpoint test where endpoint has explicit
        permission_classes, overriding the global default """

    def setUp(self):
        super(TestProjectTaskAPIPermissions, self).setUp()

        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.some_project = ProjectFactory.create(owner=self.user)
        self.projects_url = reverse('project_list')

        self.tasks_url = reverse('task_list')
        self.wallpost_url = reverse('wallpost_list')

    @mock.patch('bluebottle.clients.properties.CLOSED_SITE', True)
    def test_closed_api_readonly_permission_noauth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        response = self.client.get(self.tasks_url,
                                   {'project': self.some_project.slug})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @mock.patch('bluebottle.clients.properties.CLOSED_SITE', False)
    def test_open_api_readonly_permission_noauth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        response = self.client.get(self.tasks_url,
                                   {'project': self.some_project.slug})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch('bluebottle.clients.properties.CLOSED_SITE', True)
    def test_closed_api_readonly_permission_auth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        response = self.client.get(self.tasks_url,
                                   {'project': self.some_project.slug},
                                   token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
