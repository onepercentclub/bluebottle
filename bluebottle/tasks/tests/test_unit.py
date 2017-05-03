import datetime

from django.utils import timezone
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.models import Task
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase

# import taskmail in order to properly register mail handlers. Without it tests mail fail
from bluebottle.tasks import taskmail  # noqa


class TaskUnitTestBase(BluebottleTestCase):
    def setUp(self):
        super(TaskUnitTestBase, self).setUp()

        self.init_projects()
        self.status_running = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(status=self.status_running, amount_asked=0)
        self.task = TaskFactory.create(
            project=self.project,
        )


class TestDeadline(TaskUnitTestBase):
    """
    Test what happens when a task reaches it's deadline
    """
    def setUp(self):
        super(TestDeadline, self).setUp()

        self.task.deadline = timezone.now() - datetime.timedelta(days=1)
        self.task.save()

    def test_deadline_realised(self):
        self.task.people_needed = 2
        self.task.save()

        TaskMemberFactory.create(task=self.task, status='accepted')

        self.task.deadline_reached()

        self.assertEqual(self.task.status, Task.TaskStatuses.realized)

    def test_deadline_closed(self):
        self.task.status = Task.TaskStatuses.open
        self.task.deadline_reached()

        self.assertEqual(self.task.status, Task.TaskStatuses.closed)


@override_settings(CELERY_RESULT_BACKEND=None)
class TestTaskRealised(TaskUnitTestBase):
    """
    Test the status of a project when a task is realised
    """
    def test_all_tasks_realised(self):
        self.task.status = Task.TaskStatuses.realized
        self.task.save()

        self.assertEqual(self.task.status, Task.TaskStatuses.realized)
        self.assertEqual(self.project.status.slug, 'done-complete')

    def test_some_tasks_realised(self):
        TaskFactory.create(project=self.project, status=Task.TaskStatuses.in_progress)
        self.task.status = Task.TaskStatuses.realized
        self.task.save()

        self.assertEqual(self.task.status, Task.TaskStatuses.realized)
        self.assertEqual(self.project.status.slug, 'campaign')

    def test_all_tasks_realised_closed_project(self):
        self.project.status = ProjectPhase.objects.get(slug='done-incomplete')
        self.task.status = Task.TaskStatuses.realized
        self.task.save()

        self.assertEqual(self.task.status, Task.TaskStatuses.realized)
        self.assertEqual(self.project.status.slug, 'done-complete')
