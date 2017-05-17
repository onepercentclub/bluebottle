from datetime import timedelta, datetime

from bluebottle.projects.models import Project, ProjectPhase
from bluebottle.tasks.models import Task, Skill
from bluebottle.test.utils import BluebottleTestCase
from django.utils import timezone

from rest_framework import status

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory, \
    ProjectPhaseFactory
from bluebottle.test.factory_models.tasks import SkillFactory, TaskFactory, \
    TaskMemberFactory


class TaskApiIntegrationTests(BluebottleTestCase):
    """ Tests for tasks. """

    def setUp(self):
        super(TaskApiIntegrationTests, self).setUp()

        self.init_projects()

        self.some_user = BlueBottleUserFactory.create()
        self.some_token = "JWT {0}".format(self.some_user.get_jwt_token())

        self.another_user = BlueBottleUserFactory.create()
        self.another_token = "JWT {0}".format(self.another_user.get_jwt_token())

        self.some_project = ProjectFactory.create(owner=self.some_user)
        self.another_project = ProjectFactory.create(owner=self.another_user)

        self.skill1 = SkillFactory.create()
        self.skill2 = SkillFactory.create()
        self.skill3 = SkillFactory.create()
        self.skill4 = SkillFactory.create()

        self.task_url = '/api/bb_tasks/'
        self.task_preview_url = '/api/bb_tasks/previews/'
        self.task_members_url = '/api/bb_tasks/members/'

    def test_create_task(self):
        # Get the list of tasks for some project should return none (count = 0)
        response = self.client.get(self.task_url,
                                   {'project': self.some_project.slug},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEquals(response.data['count'], 0)

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
            'deadline': str(future_date)
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
        self.assertEquals(response.data['count'], 1)

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
            'deadline': str(self.some_project.deadline + timedelta(hours=1)),
            'deadline_to_apply': str(self.some_project.deadline + timedelta(minutes=1))
        }
        response = self.client.post(self.task_url, some_task_data,
                                    token=self.some_token)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST,
                         response.data)
        self.assertTrue('deadline' in response.data)

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
        self.task1 = TaskFactory.create(
            status=Task.TaskStatuses.in_progress,
            author=self.some_project.owner,
            project=self.some_project,
        )
        self.task2 = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.another_project.owner,
            project=self.another_project,
        )

        self.assertEqual(2, Task.objects.count())

        # Test as a different user
        response = self.client.get(self.task_url, {'status': 'open'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)

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
        self.task1 = TaskFactory.create(
            status=Task.TaskStatuses.in_progress,
            author=self.some_project.owner,
            project=self.some_project,
            deadline=timezone.datetime(2010, 05, 05, tzinfo=timezone.get_current_timezone())
        )
        self.task2 = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.another_project.owner,
            project=self.another_project,
            deadline=timezone.datetime(2011, 05, 05, tzinfo=timezone.get_current_timezone())
        )

        self.assertEqual(2, Project.objects.count())
        self.assertEqual(2, Task.objects.count())

        api_url = self.task_preview_url

        # test that only one task preview is returned

        response = self.client.get(api_url, token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(api_url, {'status': 'in progress'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)

        response = self.client.get(api_url, {'status': 'open'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 0)

        skill = self.task1.skill
        response = self.client.get(api_url, {'skill': skill.id},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.task1.id)

        response = self.client.get(api_url, {'before': '2011-01-01'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.task1.id)

        response = self.client.get(api_url, {'after': '2011-01-01'},
                                   token=self.some_token)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         response.data)
        self.assertEqual(response.data['count'], 0)

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

    def test_get_correct_base_task_fields(self):
        """ Test that the fields defined in the BaseTask serializer are returned in the response """

        task = TaskFactory.create()

        response = self.client.get('{0}{1}'.format(self.task_url, task.id),
                                   token=self.some_token)

        # Fields as defined in the serializer
        serializer_fields = (
            'id', 'members', 'files', 'project', 'skill', 'author', 'status',
            'description', 'location', 'deadline', 'time_needed', 'title',
            'people_needed'
        )

        for field in serializer_fields:
            self.assertTrue(field in response.data)


class TestTaskSearchCase(BluebottleTestCase):
    """Tests for the task search functionality."""

    def setUp(self):
        """Setup reusable data."""
        self.init_projects()

        self.now = datetime.combine(timezone.now(), datetime.min.time())
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

        response = self.client.get(self.task_url, search_date,
                                   token=self.some_token)

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
        event_task_3 = TaskFactory.create(status='open',
                                          type='event',
                                          deadline=self.now + timezone.timedelta(days=3),
                                          people_needed=1)

        search_date = {
            'start': str((self.now + timezone.timedelta(days=3)))
        }

        response = self.client.get(self.task_url, search_date,
                                   token=self.some_token)

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
