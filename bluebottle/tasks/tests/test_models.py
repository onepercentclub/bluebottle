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

    def test_check_number_of_members_needed_no_externals_count(self):
        """ Test that 'check_number_of_members_needed' returns the right count without externals"""
        task = TaskFactory.create(status='open', people_needed=4)

        task_member1 = TaskMemberFactory.create(task=task, status='accepted')
        self.assertEqual(task_member1.task.people_accepted, 1)

        task_member2 = TaskMemberFactory.create(task=task, status='accepted')
        self.assertEqual(task_member2.task.people_accepted, 2)
        self.assertEqual(task_member1.task.people_accepted, 2)

    def test_check_number_of_members_needed_with_externals_count(self):
        """ Test that 'check_number_of_members_needed' returns the right count with externals"""
        task = TaskFactory.create(status='open', people_needed=4)

        task_member1 = TaskMemberFactory.create(task=task, status='accepted',
                                                externals=1)
        self.assertEqual(task_member1.task.people_accepted, 2)

        task_member2 = TaskMemberFactory.create(task=task, status='accepted',
                                                externals=2)
        self.assertEqual(task_member2.task.people_accepted, 5)
        self.assertEqual(task_member1.task.people_accepted, 5)

    def test_check_number_of_members_needed_set_in_progress(self):
        """ Test that the task status changes when enough people are accepted for a task. It shouldn't update 
            when insufficient people are accepted."""
        task = TaskFactory.create(status='open', people_needed=4)

        task_member1 = TaskMemberFactory.create(task=task, status='accepted',
                                                externals=1)

        self.assertEqual(task_member1.task.people_accepted, 2)
        # Not enough people yet
        self.assertEqual(task.status, 'open')

        task_member2 = TaskMemberFactory.create(task=task, status='accepted',
                                                externals=2)

        self.assertEqual(task_member2.task.people_accepted, 5)
        # More than people_needed have applied
        self.assertEqual(task.status, 'in progress')


class TestTaskCase(BluebottleTestCase):
    def setUp(self):
        self.init_projects()

    def test_save_check_status_update_insufficent_accepted_members(self):
        """ Check that the save method correctly sets the status of the task if not enough task members are 
            accepted for the task and the save method is called """
        task = TaskFactory.create(status='open', people_needed=4)
        task_member1 = TaskMemberFactory.create(task=task, status='accepted',
                                                externals=1)
        task.save()

        self.assertEqual(task.status, 'open')

        task_member2 = TaskMemberFactory.create(task=task, status='accepted')
        task.save()

        # Total of 3 out of 4 people. Task status should be open.
        self.assertEqual(task.status, 'open')

    def test_save_check_status_update_sufficent_accepted_members(self):
        """ Check that the save method correctly sets the status of the task if enough task members are 
            accepted for the task and the save method is called """
        task = TaskFactory.create(status='open', people_needed=2)
        task_member1 = TaskMemberFactory.create(task=task, status='accepted',
                                                externals=1)
        task.save()

        self.assertEqual(task.status, 'in progress')


class TestTaskSearchDate(BluebottleTestCase):

    def test_day_start_method(self):
        from bluebottle.bb_tasks.views import day_start

        date_str = '2016-08-09T15:45:29.275632Z'
        result = day_start(date_str)
        self.assertEqual(result.time(), timezone.datetime(2016, 8, 9, 0, 0).time())
        self.assertEqual(result.date(), timezone.datetime(2016, 8, 9, 0, 0).date())

        date_str = '2016-08-09T23:45:29.275632Z'
        result = day_start(date_str)
        self.assertEqual(result.time(), timezone.datetime(2016, 8, 9, 0, 0).time())
        self.assertEqual(result.date(), timezone.datetime(2016, 8, 9, 0, 0).date())

        date_str = '2016-08-09T00:15:29.275632Z'
        result = day_start(date_str)
        self.assertEqual(result.time(), timezone.datetime(2016, 8, 9, 0, 0).time())
        self.assertEqual(result.date(), timezone.datetime(2016, 8, 9, 0, 0).date())


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
