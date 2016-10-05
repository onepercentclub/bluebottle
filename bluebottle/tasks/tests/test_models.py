from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.tasks.models import TaskStatusLog, TaskMemberStatusLog


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
