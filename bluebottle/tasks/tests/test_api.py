from datetime import timedelta
import mock
import time
import urllib

from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.signing import TimestampSigner
from django.core.urlresolvers import reverse
from django.utils import timezone

from rest_framework import status

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.models import Task, TaskMember
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
        self.tasks_url = reverse('task-list')
        self.task_member_url = reverse('task-member-list')

    def test_task_count(self):
        """
        Test various task_count values
        """

        # No task members assigned to a task of a project, so there is a task open
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['open_task_count'], 1)
        self.assertEqual(response.data['results'][0]['task_count'], 1)

        TaskMemberFactory.create(member=self.another_user,
                                 task=self.task1,
                                 status='accepted')

        # The task has one task member and two people needed, still one task open
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['open_task_count'], 1)
        self.assertEqual(response.data['results'][0]['task_count'], 1)

        task_member2 = TaskMemberFactory.create(member=self.yet_another_user,
                                                task=self.task1,
                                                status='accepted')

        # The task has two accepted task members for two people_needed, no more task open
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['open_task_count'], 0)
        self.assertEqual(response.data['results'][0]['task_count'], 1)

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
        self.assertEqual(response.data['results'][0]['open_task_count'], 0)
        self.assertEqual(response.data['results'][0]['realized_task_count'], 0)

        self.task1.status = Task.TaskStatuses.realized
        self.task1.save()

        # The task is realized, so don't give a task_count
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 1)
        self.assertEqual(response.data['results'][0]['open_task_count'], 0)
        self.assertEqual(response.data['results'][0]['realized_task_count'], 1)

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
        task_member_url = reverse('task-member-detail', kwargs={'pk': task_member_id})
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
        task_member_url = reverse('task-member-detail', kwargs={'pk': task_member_id})
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
        task_member_url = reverse('task-member-detail', kwargs={'pk': task_member_id})
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

    def test_task_member_duplicate(self):
        task = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.some_project,
            people_needed=1
        )

        TaskMemberFactory.create(
            member=self.some_user, task=task, status='applied'
        )

        task_member_data = {
            'task': task.id,
            'motivation': 'Pick me!'
        }
        response = self.client.post(self.task_member_url,
                                    task_member_data,
                                    HTTP_AUTHORIZATION=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_task_member_rejected(self):
        task = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.some_project,
            people_needed=1
        )

        TaskMemberFactory.create(
            member=self.some_user, task=task, status='rejected'
        )

        task_member_data = {
            'task': task.id,
            'motivation': 'Pick me!'
        }
        response = self.client.post(self.task_member_url,
                                    task_member_data,
                                    HTTP_AUTHORIZATION=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_task_member_confirm_as_taskmember(self):
        task = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.some_project,
            people_needed=1
        )

        TaskMemberFactory.create(
            member=self.some_user, task=task, status='accepted'
        )
        task_member = TaskMemberFactory.create(
            member=self.another_user, task=task, status='accepted'
        )
        data = {
            'status': 'realized',
            'task': task.pk,
            'message': 'Just a test message\nWith a newline'
        }

        task_member_url = reverse('task-member-detail', kwargs={'pk': task_member.pk})
        response = self.client.put(task_member_url, data=data, token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_time_spent(self):
        task = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.some_project,
            people_needed=4,
            time_needed=8
        )

        task_member_data = {
            'task': task.id,
            'motivation': 'Pick me!'
        }

        response = self.client.post(self.task_member_url,
                                    task_member_data,
                                    HTTP_AUTHORIZATION=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_member1_id = response.data['id']
        task_member1_url = reverse('task-member-detail', kwargs={'pk': task_member1_id})

        response = self.client.post(self.task_member_url,
                                    task_member_data,
                                    HTTP_AUTHORIZATION=self.yet_another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        task_member2_id = response.data['id']
        task_member2_url = reverse('task-member-detail', kwargs={'pk': task_member2_id})

        # Check that if we don't specify time spent it uses the time_needed froem task.
        response = self.client.patch(task_member1_url,
                                     {'status': 'realized'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['time_spent'], 8)

        # Check that we can individually edit task member time spent.
        response = self.client.patch(task_member2_url,
                                     {'status': 'realized', 'time_spent': '7'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['time_spent'], 7)

    def test_task_member_resume(self):
        task = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.some_project,
            people_needed=4,
            time_needed=8
        )

        resume_file = open(
            './bluebottle/projects/test_images/upload.png',
            mode='rb'
        )

        task_member_data = {
            'task': task.id,
            'resume': resume_file,
            'motivation': 'Pick me!'
        }

        response = self.client.post(
            self.task_member_url,
            task_member_data,
            token=self.another_token,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        resume = response.data['resume']
        self.assertTrue(
            resume['url'].startswith('/downloads/taskmember/resume')
        )
        self.assertTrue(
            resume['name'].startswith('upload')
        )

        task_member = TaskMember.objects.get(pk=response.data['id'])
        self.assertTrue(
            task_member.resume.name.startswith('private')
        )

    def test_task_member_without_resume(self):
        task = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.some_project,
            people_needed=4,
            time_needed=8
        )

        task_member_data = {
            'task': task.id,
            'motivation': 'Pick me!'
        }

        response = self.client.post(
            self.task_member_url,
            task_member_data,
            token=self.another_token,
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(response.data['resume'], None)

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

    def test_deadline_no_project_deadline(self):
        """
        A task for a project without a deadline should not validate the deadline.
        """
        self.some_project.deadline = None
        self.some_project.status = ProjectPhase.objects.get(slug='plan-new')
        self.some_project.campaign_duration = 10
        self.some_project.save()
        task_data = {
            'people_needed': 1,
            'deadline': timezone.now() + timedelta(weeks=2),
            'deadline_to_apply': timezone.now() + timedelta(weeks=1),
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

    def test_deadline_before_project_deadline(self):
        """
        A task should have a deadline before the project deadline
        """
        task_data = {
            'people_needed': 1,
            'deadline': '2015-08-09T12:45:14.134756',
            'deadline_to_apply': self.some_project.deadline + timedelta(weeks=1),
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deadline_before_deadline_to_apply(self):
        """
        Test the setting of the deadline of a Task on save to the end of a day.
        """
        task_data = {
            'people_needed': 1,
            'deadline': '2016-08-09T12:45:14.134756',
            'deadline_to_apply': '2016-08-10:45:14.134756',
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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_taskmembers_inactive_projects(self):
        """
        Test that user can only apply for a Task for a running Project (status=campaign)
        """

        submitted = ProjectPhase.objects.get(slug='plan-submitted')
        rejected = ProjectPhase.objects.get(slug='plan-submitted')
        realised = ProjectPhase.objects.get(slug='done-complete')
        campaign = ProjectPhase.objects.get(slug='campaign')

        task = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.some_project,
            people_needed=1
        )
        task_member_data = {
            'task': task.id,
            'motivation': 'Pick me!'
        }

        # Can't apply for tasks for submitted projects
        self.some_project.status = submitted
        self.some_project.save()
        response = self.client.post(
            self.task_member_url,
            task_member_data,
            token=self.some_token
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN,
                         "Can't apply for tasks for submitted projects")

        # Can't apply for tasks for rejected projects
        self.some_project.status = rejected
        self.some_project.save()
        response = self.client.post(
            self.task_member_url,
            task_member_data,
            token=self.some_token
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN,
                         "Can't apply for tasks for rejected projects")

        # Can't apply for tasks for realised projects
        self.some_project.status = realised
        self.some_project.save()
        response = self.client.post(
            self.task_member_url,
            task_member_data,
            token=self.some_token
        )
        self.assertEqual(response.status_code,
                         status.HTTP_403_FORBIDDEN,
                         "Can't apply for tasks for realised projects")

        # Can apply for tasks for campaigning projects
        self.some_project.status = campaign
        self.some_project.save()
        response = self.client.post(
            self.task_member_url,
            task_member_data,
            token=self.some_token
        )
        self.assertEqual(response.status_code,
                         status.HTTP_201_CREATED,
                         "Can apply for tasks for campaigning projects")

    def test_task_project_role_permissions(self):
        """
        Test task_manager and owner roles when creating tasks
        """
        self.some_project.owner = self.some_user
        self.some_project.task_manager = self.another_user
        self.some_project.save()

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

        # Task manager should have rights to create a task
        response = self.client.post(self.tasks_url, task_data,
                                    HTTP_AUTHORIZATION=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Project owner should be allowed to see the tasks
        response = self.client.get(self.tasks_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        permissions = response.data['results'][0]['permissions']

        self.assertEqual(permissions['GET'], True)
        self.assertEqual(permissions['PUT'], False)

        # Project owner should not be allowed to create a task
        response = self.client.post(self.tasks_url, task_data,
                                    HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_taskmember_project_role_permissions(self):
        """
        Test task_manager and owner roles when accepting task members
        """
        self.some_project.owner = self.some_user
        self.some_project.task_manager = self.another_user
        self.some_project.save()

        task = TaskFactory(project=self.some_project, author=self.another_user)
        task_member = TaskMemberFactory(task=task, status='applied')

        # Project owner should be allowed to see taskmember
        task_member_url = reverse('task-member-detail', kwargs={'pk': task_member.id})
        response = self.client.get(task_member_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Project owner should be disallowed to accept taskmember
        task_member_url = reverse('task-member-detail', kwargs={'pk': task_member.id})
        response = self.client.patch(task_member_url,
                                     {'status': 'accepted'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Task manager should have rights to accept taskmember
        task_member_url = reverse('task-member-detail', kwargs={'pk': task_member.id})
        response = self.client.patch(task_member_url,
                                     {'status': 'accepted'},
                                     HTTP_AUTHORIZATION=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task = TaskFactory(project=self.some_project, author=self.another_user)
        task_member = TaskMemberFactory(task=task, status='applied')

        self.some_project.task_manager = self.some_user
        self.some_project.save()

        # Project owner should be disallowed to accept taskmember
        task_member_url = reverse('task-member-detail', kwargs={'pk': task_member.id})
        response = self.client.patch(task_member_url,
                                     {'status': 'accepted'},
                                     HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TaskMemberResumeTest(BluebottleTestCase):
    def setUp(self):
        super(TaskMemberResumeTest, self).setUp()

        self.init_projects()
        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_token = "JWT {0}".format(self.another_user.get_jwt_token())

        self.task = TaskFactory.create(
            project=ProjectFactory.create(owner=self.some_user),
        )

        self.member = TaskMemberFactory.create(
            task=self.task,
            member=self.another_user,
            resume='private/tasks/resume/test.jpg'
        )
        self.signer = TimestampSigner()

        self.resume_url = reverse('task-member-resume', args=(self.member.id, ))
        self.task_member_url = reverse('task-member-detail', args=(self.member.id, ))

    def test_task_member_detail_includes_download_url_task_owner(self):
        response = self.client.get(
            self.task_member_url, token=self.some_token
        )
        self.assertTrue(
            response.data['resume']['url'].startswith('/downloads/taskmember/resume/')
        )
        self.assertEqual(
            response.data['resume']['name'],
            'test.jpg'
        )

    def test_task_member_detail_includes_download_url_task_member(self):
        response = self.client.get(
            self.task_member_url, token=self.another_token
        )
        self.assertTrue(
            response.data['resume']['url'].startswith('/downloads/taskmember/resume/')
        )
        self.assertEqual(
            response.data['resume']['name'],
            'test.jpg'
        )

    def test_task_member_detail_includes_download_url_other_user(self):
        response = self.client.get(
            self.task_member_url,
            token="JWT {0}".format(
                BlueBottleUserFactory.create().get_jwt_token()
            )
        )
        self.assertIsNone(
            response.data.get('resume')
        )

    def test_task_member_detail_includes_download_url_anonymous(self):
        response = self.client.get(
            self.task_member_url
        )
        self.assertIsNone(
            response.data.get('resume')
        )

    def test_task_member_resume_signed(self):
        signature = self.signer.sign(self.resume_url)
        response = self.client.get(
            '{}?{}'.format(self.resume_url, urllib.urlencode({'signature': signature}))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['x-accel-redirect'],
            '/media/private/tasks/resume/test.jpg'
        )

    def test_task_member_resume_no_signature(self):
        response = self.client.get(
            self.resume_url
        )
        self.assertEqual(response.status_code, 404)

    def test_task_member_resume_incorrect_signature(self):
        response = self.client.get(
            '{}?{}'.format(
                self.resume_url,
                urllib.urlencode({'signature': '{}:blabla'.format(self.resume_url)}))
        )
        self.assertEqual(response.status_code, 404)

    def test_task_member_resume_expired_signature(self):
        current_time = time.time()

        with mock.patch.object(time, 'time', return_value=current_time - (7 * 60 * 60)):
            signature = self.signer.sign(self.resume_url)

        response = self.client.get(
            '{}?{}'.format(self.resume_url, urllib.urlencode({'signature': signature}))
        )
        self.assertEqual(response.status_code, 404)

    def test_task_member_resume_expired_non_signature(self):
        current_time = time.time()

        with mock.patch.object(time, 'time', return_value=current_time - (3 * 60 * 60)):
            signature = self.signer.sign(self.resume_url)

        response = self.client.get(
            '{}?{}'.format(self.resume_url, urllib.urlencode({'signature': signature}))
        )
        self.assertEqual(response.status_code, 200)


class TestMyTasksPermissions(BluebottleTestCase):
    """
    Test methods for getting tasks that you are a member of.
    """

    def setUp(self):
        super(TestMyTasksPermissions, self).setUp()

        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.project = ProjectFactory.create(task_manager=self.user)

        self.my_task_member_url = reverse('my_task_member_list')

    def test_closed_api_readonly_permission_task_manager(self):
        """
        External task manager should get empty list for own task membership, not 403.
        """
        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_read_taskmember')
        )
        authenticated.permissions.add(
            Permission.objects.get(codename='api_read_own_taskmember')
        )

        response = self.client.get(self.my_task_member_url, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestTaskMemberStatusAPI(BluebottleTestCase):
    """
    Test methods for getting tasks that you are a member of.
    """

    def setUp(self):
        super(TestTaskMemberStatusAPI, self).setUp()

        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.member = BlueBottleUserFactory.create()

        self.user_token = "JWT {0}".format(self.user.get_jwt_token())

        self.project = ProjectFactory.create(task_manager=self.user)
        self.task = TaskFactory.create(project=self.project, people_needed=2)
        self.task_member = TaskMemberFactory.create(
            task=self.task, member=self.member, status='applied'
        )

        self.url = reverse('task-member-status', args=(self.task_member.pk, ))

    def test_read(self):
        """
        Task mamangers can read the status
        """
        response = self.client.get(self.url, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.keys(), ['id', 'member', 'status', 'permissions'])

    def test_set_status_accepted(self):
        """
        Task mamangers can read the status
        """
        mail.outbox = []
        data = {
            'status': 'accepted',
            'message': 'Just a test message\nWith a newline'
        }
        response = self.client.put(self.url, data=data, token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'accepted')

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(
            data['message'].replace('\n', '<br />') in mail.outbox[0].alternatives[0][0]
        )
        self.assertTrue(
            data['message'] in mail.outbox[0].body
        )

    def test_set_status_accepted_twice(self):
        """
        Task mamangers can read the status
        """
        mail.outbox = []
        data = {
            'status': 'accepted',
            'message': 'Just a test message\nWith a newline'
        }
        response = self.client.put(self.url, data=data, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.put(self.url, data=data, token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(mail.outbox), 1)

    def test_set_status_rejected(self):
        """
        Task mamangers can read the status
        """
        mail.outbox = []
        data = {
            'status': 'rejected',
            'message': 'Just a test message'
        }
        response = self.client.put(self.url, data=data, token=self.user_token)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rejected')

        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(
            'https://testserver/projects' in mail.outbox[0].alternatives[0][0]
        )
        self.assertTrue(
            data['message'] in mail.outbox[0].alternatives[0][0]
        )
        self.assertTrue(
            data['message'] in mail.outbox[0].body
        )
        self.assertTrue(
            'https://testserver/projects' in mail.outbox[0].body
        )

    def test_set_status_member(self):
        """
        Task mamangers can read the status
        """
        data = {
            'status': 'accepted',
            'message': 'Just a test message'
        }

        token = "JWT {0}".format(self.member.get_jwt_token())
        response = self.client.put(self.url, data=data, token=token)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestProjectTaskAPIPermissions(BluebottleTestCase):
    """
    API endpoint test where endpoint has explicit
    permission_classes, overriding the global default
    """

    def setUp(self):
        super(TestProjectTaskAPIPermissions, self).setUp()

        self.init_projects()

        self.user = BlueBottleUserFactory.create()
        self.user_token = "JWT {0}".format(self.user.get_jwt_token())
        self.some_project = ProjectFactory.create(owner=self.user)
        self.projects_url = reverse('project_list')

        self.tasks_url = reverse('task-list')
        self.wallpost_url = reverse('wallpost_list')

    def test_closed_api_readonly_permission_noauth(self):
        """ an endpoint with an explicit *OrReadOnly permission
            should still be closed """
        anonymous = Group.objects.get(name='Anonymous')
        anonymous.permissions.remove(
            Permission.objects.get(codename='api_read_task')
        )

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
        anonymous = Group.objects.get(name='Anonymous')
        anonymous.permissions.remove(
            Permission.objects.get(codename='api_read_wallpost')
        )

        response = self.client.get(self.tasks_url,
                                   {'project': self.some_project.slug},
                                   token=self.user_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_related_permissions(self):
        TaskFactory.create(project=self.some_project)
        response = self.client.get(self.tasks_url,
                                   token=self.user_token)

        self.assertTrue(
            response.data['results'][0]['related_permissions']['task_members']['POST']
        )

    def test_related_permissions_no_owner_permission(self):
        TaskFactory.create(project=self.some_project)
        authenticated = Group.objects.get(name='Authenticated')
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_add_own_taskmember')
        )
        authenticated.permissions.remove(
            Permission.objects.get(codename='api_add_taskmember')
        )

        response = self.client.get(self.tasks_url,
                                   token=self.user_token)

        self.assertFalse(
            response.data['results'][0]['related_permissions']['task_members']['POST']
        )
