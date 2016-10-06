from django.utils import timezone

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.tasks.models import TaskMember, Task, TaskStatusLog, TaskMemberStatusLog


class TestTaskMemberCase(BluebottleTestCase):
    def setUp(self):
        self.init_projects()

    def test_task_realized_when_members_realized(self):
        """
        If all the task members are realized after the deadline for a task which
        is not yet realized (eg. closed) then the task should also be realized.
        """
        deadline = timezone.now() - timezone.timedelta(days=1)
        task = TaskFactory.create(deadline=deadline, status='closed', people_needed=2)
        task_member1 = TaskMemberFactory.create(task=task, status='accepted')
        task_member2 = TaskMemberFactory.create(task=task, status='accepted')

        task_member1.status = TaskMember.TaskMemberStatuses.realized
        task_member1.save()
        task_member2.status = TaskMember.TaskMemberStatuses.realized
        task_member2.save()

        self.assertEqual(task.status, Task.TaskStatuses.realized)


class TestTaskStatusLog(BluebottleTestCase):
    def setUp(self):
        self.init_projects()

    def test_task_status_log_creation(self):
        task = TaskFactory.create(status='open', people_needed=4)
        task.save()
        log = TaskStatusLog.objects.first()

        self.assertEqual(TaskStatusLog.objects.count(), 1)
        self.assertEqual(log.status, 'open')
        self.assertEqual(log.task_id, task.id)


class TestTaskMemberStatusLog(BluebottleTestCase):
    def setUp(self):
        self.init_projects()

    def test_task_status_log_creation(self):
        task_member = TaskMemberFactory.create(status='applied')
        task_member.save()
        log = TaskMemberStatusLog.objects.first()

        self.assertEqual(TaskStatusLog.objects.count(), 1)
        self.assertEqual(log.status, 'applied')
        self.assertEqual(log.task_member_id, task_member.id)

