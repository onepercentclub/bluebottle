from datetime import timedelta, datetime
import mock

from django.contrib.auth.models import Group, Permission
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils import timezone

from rest_framework import status

from bluebottle.projects.models import Project, ProjectPhase
from bluebottle.tasks.models import Task, Skill, TaskMember
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory, SkillFactory


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

        self.yet_another_user = BlueBottleUserFactory.create()
        self.yet_another_token = "JWT {0}".format(
            self.yet_another_user.get_jwt_token()
        )

        self.task = TaskFactory.create(
            author=self.some_user
        )

        self.member = TaskMemberFactory.create(
            task=self.task,
            member=self.another_user,
            resume='private/tasks/resume/test.jpg'
        )
        self.resume_url = reverse('task-member-resume', args=(self.member.id, ))

    def test_task_member_resume_download_member(self):
        response = self.client.get(
            self.resume_url, token=self.another_token
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['x-accel-redirect'],
            '/media/private/tasks/resume/test.jpg'
        )

    def test_task_member_resume_download_task_owner(self):
        response = self.client.get(
            self.resume_url, token=self.some_token
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['x-accel-redirect'],
            '/media/private/tasks/resume/test.jpg'
        )

    def test_task_member_resume_download_task_anonymous(self):
        response = self.client.get(self.resume_url)
        self.assertEqual(response.status_code, 401)

    def test_task_member_resume_download_unrelated_user(self):
        response = self.client.get(
            self.resume_url, token=self.yet_another_token
        )
        self.assertEqual(response.status_code, 403)

    def test_task_member_resume_download_staff_session(self):
        self.yet_another_user.groups.add(
            Group.objects.get(name='Staff')
        )

        self.client.force_login(self.yet_another_user)
        response = self.client.get(
            self.resume_url, token=self.yet_another_token
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response['x-accel-redirect'],
            '/media/private/tasks/resume/test.jpg'
        )

    def test_task_member_resume_download_non_staff_session(self):
        self.client.force_login(self.yet_another_user)
        response = self.client.get(
            self.resume_url, token=self.yet_another_token
        )

        self.assertEqual(response.status_code, 403)


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


class TaskApiIntegrationTests(BluebottleTestCase):
    """ Tests for tasks. """

    def setUp(self):
        super(TaskApiIntegrationTests, self).setUp()

        self.init_projects()

        campaign = ProjectPhase.objects.get(slug='campaign')

        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())
        self.some_project = ProjectFactory.create(owner=self.some_user, status=campaign)

        self.another_user = BlueBottleUserFactory.create()
        self.another_token = "JWT {0}".format(self.another_user.get_jwt_token())
        self.another_project = ProjectFactory.create(owner=self.another_user)

        self.task = TaskFactory.create(project=self.some_project)

        self.skill1 = SkillFactory.create()
        self.skill2 = SkillFactory.create()
        self.skill3 = SkillFactory.create()
        self.skill4 = SkillFactory.create()

        self.task_url = reverse('task-list')
        self.task_preview_url = reverse('task_preview_list')
        self.task_members_url = reverse('task-member-list')
        self.task_detail_url = reverse('task_detail', args=(self.task.pk, ))

    def test_create_task(self):
        # Get the list of tasks for some project should return none (count = 0)
        response = self.client.get(self.task_url,
                                   {'project': self.some_project.slug},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEquals(response.data['count'], 1)

        future_date = timezone.now() + timezone.timedelta(days=30)

        # Now let's create a task.
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': str(future_date),
            'deadline_to_apply': str(future_date - timedelta(days=1))
        }
        response = self.client.post(self.task_url, some_task_data,
                                    token=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)
        self.assertEquals(response.data['title'], some_task_data['title'])
        self.assertEquals(response.data['location'], some_task_data['location'])
        some_task_url = "{0}{1}".format(self.task_url, response.data['id'])

        # Create a task for a project you don't own should fail...
        another_task_data = {
            'project': self.another_project.slug,
            'title': 'Translate some text.',
            'description': 'Wie kan in engels vertalen?',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill2.id),
            'location': 'Tiel',
            'deadline': str(future_date),
            'deadline_to_apply': str(future_date - timedelta(days=1))
        }
        response = self.client.post(self.task_url, another_task_data,
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         response.data)

        # By now the list for this project should contain one task
        response = self.client.get(self.task_url,
                                   {'project': self.some_project.slug},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEquals(response.data['count'], 2)

        # Another user that owns another project can create a task for that.
        another_task_data = {
            'project': self.another_project.slug,
            'title': 'Translate some text.',
            'description': 'Wie kan Engels vertalen?',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill3.id),
            'location': 'Tiel',
            'deadline': str(future_date),
            'deadline_to_apply': str(future_date - timedelta(days=1))
        }
        response = self.client.post(self.task_url, another_task_data,
                                    token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)
        self.assertEquals(response.data['title'], another_task_data['title'])

        # Go wild! Add another task to that project add some tags this time --> NO TAGS ANYMORE
        # Because we have a nesting here we should properly encode it as json
        third_task_data = {
            'project': self.another_project.slug,
            'title': 'Translate some text.',
            'description': 'Wie kan Engels vertalen?',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill4.id),
            'location': 'Tiel',
            'deadline': str(future_date),
            'deadline_to_apply': str(future_date - timedelta(days=1))
        }
        response = self.client.post(self.task_url, third_task_data,
                                    token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)
        self.assertEquals(response.data['title'], third_task_data['title'])

        # By now the list for the second project should contain two tasks
        response = self.client.get(self.task_url,
                                   {'project': self.another_project.slug},
                                   token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEquals(response.data['count'], 2)

        # Viewing task detail for the first task (other owner) should work
        response = self.client.get(some_task_url, token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEquals(response.data['title'], some_task_data['title'])

    def test_create_task_incorrect_deadline(self):
        # Create a task with an invalid deadline
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': str(self.some_project.campaign_started + timedelta(days=400)),
            'deadline_to_apply': str(self.some_project.deadline + timedelta(minutes=1))
        }
        response = self.client.post(self.task_url, some_task_data,
                                    token=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)
        self.assertTrue('deadline' in response.data)

    def test_create_task_after_project_deadline(self):
        self.some_project.project_type = 'sourcing'
        self.some_project.save()

        # Create a task with an later deadline
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': str(self.some_project.deadline + timedelta(days=1)),
            'deadline_to_apply': str(self.some_project.deadline + timedelta(minutes=1))
        }
        response = self.client.post(self.task_url, some_task_data,
                                    token=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)
        self.assertEqual(
            Task.objects.get(
                pk=response.data['id']
            ).deadline.strftime("%Y-%m-%d %H:%M:%S"),
            Project.objects.get(
                pk=self.some_project.pk
            ).deadline.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def test_create_task_after_funding_project_deadline(self):
        self.some_project.project_type = 'funding'
        self.some_project.save()

        # Create a task with an later deadline
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': str(self.some_project.deadline + timedelta(days=1)),
            'deadline_to_apply': str(self.some_project.deadline + timedelta(minutes=1))
        }
        response = self.client.post(self.task_url, some_task_data,
                                    token=self.some_token)

        # This should fail because
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)

    def test_create_task_project_not_started(self):
        self.some_project.status = ProjectPhase.objects.get(slug='plan-submitted')
        self.some_project.project_type = 'sourcing'
        self.some_project.save()

        # Create a task with an invalid deadline
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': str(self.some_project.deadline + timedelta(days=1)),
            'deadline_to_apply': str(self.some_project.deadline + timedelta(minutes=1))
        }
        response = self.client.post(self.task_url, some_task_data,
                                    token=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)

    def test_create_task_closed_project(self):
        self.some_project.status = ProjectPhase.objects.get(slug='closed')
        self.some_project.save()

        future_date = timezone.now() + timezone.timedelta(days=30)

        # Now let's create a task.
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': str(future_date),
            'deadline_to_apply': str(future_date - timezone.timedelta(days=1))
        }

        response = self.client.post(self.task_url, some_task_data,
                                    token=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)
        self.assertTrue('closed projects' in response.data[0])

    def test_update_deadline(self):
        self.some_project.project_type = 'sourcing'
        self.some_project.save()
        future_date = timezone.now() + timezone.timedelta(days=30)
        task_data = {
            'project': self.some_project.slug,
            'title': 'Some new title',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': str(self.some_project.deadline + timedelta(days=1)),
            'deadline_to_apply': str(future_date - timezone.timedelta(days=1))
        }

        response = self.client.put(
            self.task_detail_url, task_data, token=self.some_token
        )
        self.task = Task.objects.get(pk=self.task.pk)
        self.some_project = Project.objects.get(pk=self.some_project.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            self.task.deadline.strftime("%Y-%m-%d %H:%M:%S"),
            self.some_project.deadline.strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.assertEqual(
            self.task.title, task_data['title']
        )

    def test_apply_for_task(self):
        future_date = timezone.now() + timezone.timedelta(days=60)

        # let's create a task.
        some_task_data = {
            'project': self.some_project.slug,
            'title': 'A nice task!',
            'description': 'Well, this is nice',
            'time_needed': 5,
            'skill': '{0}'.format(self.skill1.id),
            'location': 'Overthere',
            'deadline': str(future_date),
            'deadline_to_apply': str(future_date - timedelta(days=1))
        }
        response = self.client.post(self.task_url, some_task_data,
                                    token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)

        response = self.client.post(self.task_members_url, {'task': response.data['id']},
                                    token=self.another_token)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         response.data)
        self.assertEquals(response.data['status'], 'applied')

    def test_task_search_by_status(self):
        """
        Ensure we can filter task list by status
        """
        TaskFactory.create(
            status=Task.TaskStatuses.in_progress,
            author=self.some_project.owner,
            project=self.some_project,
        )
        TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.another_project.owner,
            project=self.another_project,
        )

        self.assertEqual(3, Task.objects.count())

        # Test as a different user
        response = self.client.get(self.task_url, {'status': 'open'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(self.task_url, {'status': 'in progress'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)

    def test_task_preview_search(self):
        # create project phases
        phase1 = ProjectPhaseFactory.create(viewable=True)
        phase2 = ProjectPhaseFactory.create(viewable=False)

        self.some_project.status = phase1
        self.some_project.save()
        self.another_project.status = phase2
        self.another_project.save()

        # create tasks for projects
        task1 = TaskFactory.create(
            status=Task.TaskStatuses.in_progress,
            author=self.some_project.owner,
            project=self.some_project,
            deadline=timezone.datetime(2010, 05, 05, tzinfo=timezone.get_current_timezone())
        )
        TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.another_project.owner,
            project=self.another_project,
            deadline=timezone.datetime(2011, 05, 05, tzinfo=timezone.get_current_timezone())
        )

        self.assertEqual(2, Project.objects.count())
        self.assertEqual(3, Task.objects.count())

        api_url = self.task_preview_url

        # test that only one task preview is returned

        response = self.client.get(api_url, token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 2)

        response = self.client.get(api_url, {'status': 'in progress'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(api_url, {'status': 'open'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)

        skill = task1.skill
        response = self.client.get(api_url, {'skill': skill.id},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], task1.id)

        response = self.client.get(api_url, {'before': '2011-01-01'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], task1.id)

        response = self.client.get(api_url, {'after': '2011-01-01'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)

    def test_withdraw_task_member(self):
        task = TaskFactory.create()
        task_member = TaskMemberFactory.create(member=self.some_user, task=task)

        self.assertEquals(task.people_applied, 1)

        response = self.client.put(
            '{0}{1}'.format(self.task_members_url, task_member.id),
            {
                'status': 'withdrew',
                'task': task.id
            },
            token=self.some_token)

        self.assertEquals(task.people_applied, 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)

    def test_delete_task_member_no_allowed(self):
        task = TaskFactory.create()
        task_member = TaskMemberFactory.create(member=self.some_user, task=task)

        self.assertEquals(task.people_applied, 1)

        response = self.client.delete(
            '{0}{1}'.format(self.task_members_url, task_member.id),
            token=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_withdraw_task_member_unauthorized(self):
        task = TaskFactory.create()
        task_member = TaskMemberFactory.create(member=self.another_user,
                                               task=task)

        self.assertEquals(task.members.count(), 1)

        response = self.client.put(
            '{0}{1}'.format(self.task_members_url, task_member.id),
            {
                'status': 'withdrew',
                'task': task.id
            },
            token=self.some_token)

        self.assertEquals(task.members.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         response.data)

    def test_task_member_set_time_spent(self):
        task = TaskFactory.create(status=Task.TaskStatuses.open,
                                  project=self.some_project,
                                  author=self.some_user)

        task_member_user = BlueBottleUserFactory.create()
        task_member_user_token = "JWT {0}".format(task_member_user.get_jwt_token())
        task_member = TaskMemberFactory.create(member=task_member_user, task=task)

        # Only task author can set the time spent
        response1 = self.client.put('{0}{1}'.format(self.task_members_url, task_member.id),
                                    {'time_spent': 42, 'task': task.id},
                                    token=self.some_token)
        self.assertEqual(response1.status_code, status.HTTP_200_OK, response1.data)

        # Task Member cannot update his/her own time_spent
        response2 = self.client.put('{0}{1}'.format(self.task_members_url, task_member.id),
                                    {'time_spent': 5, 'task': task.id},
                                    token=task_member_user_token)
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)

        # Project owner cannot update the time_spent
        self.some_project.task_manager = BlueBottleUserFactory.create()
        self.some_project.save()
        response3 = self.client.put(
            '{0}{1}'.format(self.task_members_url, task_member.id),
            {'time_spent': 5, 'task': task.id},
            token=self.some_token)

        self.assertEqual(response3.status_code, status.HTTP_403_FORBIDDEN, response3.data)

    def test_task_member_set_time_spent_own_task_manager(self):
        task = TaskFactory.create(status=Task.TaskStatuses.open,
                                  project=self.some_project,
                                  author=self.some_user)

        task_member = TaskMemberFactory.create(member=self.some_user, task=task)

        # Only task manager can set the time spent
        response1 = self.client.put('{0}{1}'.format(self.task_members_url, task_member.id),
                                    {'time_spent': 42, 'task': task.id},
                                    token=self.some_token)
        self.assertEqual(response1.status_code, status.HTTP_200_OK, response1.data)

    def test_get_correct_base_task_fields(self):
        """ Test that the fields defined in the BaseTask serializer are returned in the response """

        task = TaskFactory.create()

        response = self.client.get('{0}{1}'.format(self.task_url, task.id),
                                   token=self.some_token)

        # Fields as defined in the serializer
        serializer_fields = ('id', 'members', 'files', 'project', 'skill', 'author', 'status', 'description',
                             'location', 'deadline', 'time_needed', 'title', 'people_needed')

        for field in serializer_fields:
            self.assertTrue(field in response.data)

    def test_get_correct_base_task_member_fields(self):
        """ Test that the fields defined in the BaseTaskMember serializer are returned in the response """

        task = TaskFactory.create()
        task_member = TaskMemberFactory.create(member=self.another_user, task=task)

        response = self.client.get('{0}{1}'.format(self.task_members_url, task_member.id), token=self.some_token)

        # Fields as defined in the serializer
        serializer_fields = (
            'id', 'member', 'status', 'created', 'motivation', 'task',
            'externals', 'time_spent', 'permissions'
        )

        for field in serializer_fields:
            self.assertTrue(field in response.data)

    def test_access_to_motivation(self):
        """ Test that the motivation can only be accessed by project owner or task member """

        task = TaskFactory.create(project=self.some_project)
        task_member = TaskMemberFactory.create(member=self.some_user, task=task, motivation="I am motivated")

        another_user_response = self.client.get('{0}{1}'.format(self.task_members_url, task_member.id),
                                                token=self.another_token)

        self.assertEqual(another_user_response.status_code, 200)
        self.assertEquals(another_user_response.data['motivation'], '')

        some_user_response = self.client.get('{0}{1}'.format(self.task_members_url, task_member.id),
                                             token=self.some_token)

        self.assertEquals(some_user_response.data['motivation'], 'I am motivated')


class TestTaskSearchCase(BluebottleTestCase):
    """Tests for the task search functionality."""

    def setUp(self):
        """Setup reusable data."""
        self.init_projects()

        self.now = datetime.combine(timezone.now(), datetime.min.time()) + timezone.timedelta(hours=3)
        self.now = timezone.get_current_timezone().localize(self.now)
        self.tomorrow = self.now + timezone.timedelta(days=1)
        self.week = self.now + timezone.timedelta(days=7)
        self.month = self.now + timezone.timedelta(days=30)

        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.task_url = '/api/bb_tasks/'

        self.event_task_1 = TaskFactory.create(status='open',
                                               title='event_task_1',
                                               type='event',
                                               deadline=self.tomorrow,
                                               people_needed=1)

        self.event_task_2 = TaskFactory.create(status='open',
                                               title='event_task_2',
                                               type='event',
                                               deadline=self.month,
                                               people_needed=1)

        self.ongoing_task_1 = TaskFactory.create(status='open',
                                                 title='ongoing_task_1',
                                                 type='ongoing',
                                                 deadline=self.week,
                                                 people_needed=1)

        self.ongoing_task_2 = TaskFactory.create(status='open',
                                                 title='ongoing_task_2',
                                                 type='ongoing',
                                                 deadline=self.tomorrow,
                                                 people_needed=1)

        self.ongoing_task_3 = TaskFactory.create(status='open',
                                                 title='ongoing_task_3',
                                                 type='ongoing',
                                                 deadline=self.month,
                                                 people_needed=1)

    def test_search_for_specific_date_no_event_task(self):
        """
        Search for tasks taking place on a specific date when
        there is no event-type task on the search date.
        """

        search_date = {
            'start': str((self.now + timezone.timedelta(days=3)))
        }

        response = self.client.get(self.task_url, search_date, token=self.some_token)

        # The result should include ongoing_task_1, ongoing_task_3 but
        # no event_tasks
        self.assertEquals(response.data['count'], 2)

        ids = [self.ongoing_task_1.id, self.ongoing_task_3.id]

        self.assertTrue(response.data['results'][0]['id'] in ids)
        self.assertTrue(response.data['results'][1]['id'] in ids)

    def test_search_for_specific_date_with_event_task(self):
        """
        Search for tasks taking place on a specific date
        when there is an event-type task.
        """
        later = self.now + timezone.timedelta(days=3)
        event_task_3 = TaskFactory.create(status='open',
                                          type='event',
                                          project=ProjectFactory(deadline=later),
                                          deadline=later,
                                          people_needed=1)

        search_date = {
            'start': str(later)
        }

        response = self.client.get(self.task_url, search_date, token=self.some_token)

        # The result should include ongoing_task_1, ongoing_task_3 and
        # event_task_3 because its on the deadline date
        ids = [self.ongoing_task_1.id, self.ongoing_task_3.id, event_task_3.id]
        self.assertEquals(response.data['count'], 3)
        self.assertIn(response.data['results'][0]['id'], ids)
        self.assertIn(response.data['results'][1]['id'], ids)
        self.assertIn(response.data['results'][2]['id'], ids)

    def test_search_for_date_range(self):
        """
        Search tasks for a date range. Return ongoing and event tasks
        with deadline in range
        """
        ongoing_task_4 = TaskFactory.create(status='open',
                                            type='ongoing',
                                            deadline=self.now +
                                            timezone.timedelta(days=365),
                                            people_needed=1)

        TaskFactory.create(status='open',
                           type='event',
                           deadline=self.now + timezone.timedelta(days=365),
                           people_needed=1)

        search_date = {
            'start': str((self.tomorrow + timezone.timedelta(days=3)).date()),
            'end': str((self.month + timezone.timedelta(days=15)).date())
        }

        response = self.client.get(self.task_url, search_date,
                                   token=self.some_token)

        # Search should return event_task_2, ongoing_task_1, and ongoing_task_3
        ids = [self.event_task_2.id, self.ongoing_task_1.id,
               self.ongoing_task_3.id, ongoing_task_4.id]
        self.assertEqual(response.data['count'], 4)
        self.assertTrue(response.data['results'][0]['id'] in ids)
        self.assertTrue(response.data['results'][1]['id'] in ids)
        self.assertTrue(response.data['results'][2]['id'] in ids)
        self.assertTrue(response.data['results'][3]['id'] in ids)

    def test_search_event_correct_timezone_awareness(self):
        """
        Test that the search for an event yields the correct
        tasks, given a task with a tricky timezone.
        """

        task = TaskFactory.create(status='open',
                                  type='event',
                                  title='task',
                                  deadline=self.now + timezone.timedelta(days=3),
                                  people_needed=1)

        task.save()

        task2 = TaskFactory.create(status='open',
                                   title='task2',
                                   type='event',
                                   deadline=self.now + timezone.timedelta(days=1, hours=23, minutes=59),
                                   people_needed=1)
        task2.save()

        task3 = TaskFactory.create(status='open',
                                   title='task3',
                                   type='event',
                                   deadline=self.now + timezone.timedelta(days=4, hours=4, minutes=0),
                                   people_needed=1)
        task3.save()

        search_date = {
            'start': str(task.deadline.date()),
            'end': str(task.deadline.date())
        }

        response = self.client.get(self.task_url, search_date, token=self.some_token)

        # Search should return task, ongoing_task_1, and ongoing_task_3
        # Task2 and Task3 should NOT be returned
        ids = [task.id, self.ongoing_task_1.id, self.ongoing_task_3.id]
        self.assertEqual(response.data['count'], 3)

        self.assertIn(response.data['results'][0]['id'], ids)
        self.assertIn(response.data['results'][1]['id'], ids)
        self.assertIn(response.data['results'][2]['id'], ids)


class ManageTaskListTests(BluebottleTestCase):
    """ Tests manage task list results """

    def setUp(self):
        super(ManageTaskListTests, self).setUp()

        self.init_projects()

        campaign = ProjectPhase.objects.get(slug='campaign')

        self.another_user = BlueBottleUserFactory.create()
        self.another_token = "JWT {0}".format(self.another_user.get_jwt_token())

        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.standard_project1 = ProjectFactory.create(task_manager=self.some_user,
                                                       status=campaign)
        self.standard_project2 = ProjectFactory.create(status=campaign)
        self.standard_project3 = ProjectFactory.create(task_manager=self.another_user,
                                                       owner=self.some_user,
                                                       status=campaign)
        self.standard_project4 = ProjectFactory.create(status=campaign)

        self.task1 = TaskFactory.create(
            status=Task.TaskStatuses.in_progress,
            project=self.standard_project1,
        )

        self.task2 = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_user,
            project=self.standard_project2,
        )

        self.task3 = TaskFactory.create(
            status=Task.TaskStatuses.open,
            project=self.standard_project3,
        )

        self.task4 = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.another_user,
            project=self.standard_project4,
        )

    def test_task_managed_list(self):
        # `some_user` can see three tasks:
        # 1) task1 because he is the author of the task manager
        # 2) task2 because he is the author (although not the task_manager)
        # 3) task3 because he is the project owner (although not the task owner or task_manager)
        response = self.client.get(reverse('my_task_list'), token=self.some_token)
        self.assertEqual(len(response.data['results']), 3)

        # `another_user` can see two tasks:
        # 1) task3 because he is the task_manager of the associated project
        # 2) task4 because he is the author (although not the task_manager)
        response = self.client.get(reverse('my_task_list'), token=self.another_token)
        self.assertEqual(len(response.data['results']), 2)


class SkillListApiTests(BluebottleTestCase):
    """ Tests for tasks. """

    def setUp(self):
        super(SkillListApiTests, self).setUp()
        # Disable 3 skills
        Skill.objects.filter(id__in=[4, 5, 6]).update(disabled=True)
        self.skill_count = Skill.objects.count()
        self.skills_url = '/api/bb_tasks/skills/'

    def test_get_list(self):
        """
        Test that the list of skills contains all but disabled skills.
        """
        response = self.client.get(self.skills_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEquals(len(response.data), self.skill_count - 3)
