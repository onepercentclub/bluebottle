from bluebottle.tasks.models import Task
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory

from bluebottle.bb_projects.models import ProjectPhase


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

        self.previews_url = '/api/bb_projects/previews/'

    def test_task_count(self):
        """ Test various task_count values """

        # No task members assigned to a task of a project, so there is a task open
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 1)

        task_member = TaskMemberFactory.create(member=self.another_user,
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

        task2 = TaskFactory.create(
            status=Task.TaskStatuses.open,
            author=self.some_project.owner,
            project=self.some_project,
            people_needed=2
        )

        # There are now two tasks for the same project, so task_count gives 2
        response = self.client.get(self.previews_url,
                                   HTTP_AUTHORIZATION=self.some_token)
        self.assertEqual(response.data['results'][0]['task_count'], 2)
