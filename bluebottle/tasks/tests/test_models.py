from datetime import timedelta

from django.core import mail
from django.utils import timezone

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.tasks.models import TaskStatusLog, TaskMemberStatusLog


class TestTaskMemberCase(BluebottleTestCase):
    def setUp(self):
        self.init_projects()

    def test_check_number_of_members_needed_no_externals_count(self):
        """ Test that 'check_number_of_members_needed' returns the right count without externals"""
        task = TaskFactory.create(status='open', people_needed=4)

        task_member1 = TaskMemberFactory.create(task=task, status='accepted')
        self.assertEqual(task_member1.task.people_accepted, 1)

        task_member2 = TaskMemberFactory.create(task=task, status='accepted')
        self.assertEqual(task_member2.task.people_accepted, 2)
        self.assertEqual(task_member1.task.people_accepted, 2)

    def test_check_number_of_members_needed_with_externals_count(self):
        """
        Test that 'check_number_of_members_needed' returns the right count with externals
        """
        task = TaskFactory.create(status='open', people_needed=4)

        task_member1 = TaskMemberFactory.create(task=task, status='accepted',
                                                externals=1)
        self.assertEqual(task_member1.task.people_accepted, 2)

        task_member2 = TaskMemberFactory.create(task=task, status='accepted',
                                                externals=2)
        self.assertEqual(task_member2.task.people_accepted, 5)
        self.assertEqual(task_member1.task.people_accepted, 5)

    def test_check_number_of_members_needed_set_in_progress(self):
        """
        Test that the task status changes when enough people are accepted for a task. It shouldn't update
        when insufficient people are accepted.
        """
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

    def test_accepting_automatic(self):
        task = TaskFactory.create(status='open', people_needed=4, accepting='automatic')

        task_member = TaskMemberFactory.create(task=task, status='applied')

        self.assertEqual(task_member.status, 'accepted')

    def test_accepting_manual(self):
        task = TaskFactory.create(status='open', people_needed=4, accepting='manual')

        task_member = TaskMemberFactory.create(task=task, status='applied')

        self.assertEqual(task_member.status, 'applied')


class TestTaskStatus(BluebottleTestCase):
    def setUp(self):
        self.init_projects()

    def test_insufficient_members(self):
        """
        Check that tasks with insufficient members are marked as 'open'
        """
        task = TaskFactory.create(status='open', people_needed=4)
        TaskMemberFactory.create(task=task, status='accepted', externals=1)
        task.save()

        self.assertEqual(task.status, 'open')

        TaskMemberFactory.create(task=task, status='accepted')
        task.save()

        # Total of 3 out of 4 people. Task status should be open.
        self.assertEqual(task.status, 'open')

    def test_sufficient_members(self):
        """
        Ongoing Tasks with sufficient members (including externals) should be in progess
        """
        task = TaskFactory.create(status='open', people_needed=2, type='ongoing')
        TaskMemberFactory.create(task=task, status='accepted', externals=1)

        self.assertEqual(task.status, 'in progress')

    def test_event_sufficient_members(self):
        """
        Ongoing Tasks with sufficient members (including externals) should be full progess
        """
        task = TaskFactory.create(status='open', people_needed=2, type='event')
        TaskMemberFactory.create(task=task, status='accepted', externals=1)

        self.assertEqual(task.status, 'full')

    def test_rejected_member(self):
        task = TaskFactory.create(status='open', people_needed=2, type='event')
        member = TaskMemberFactory.create(task=task, status='accepted', externals=1)

        self.assertEqual(task.status, 'full')

        member.status = 'rejected'
        member.save()

        self.assertEqual(task.status, 'open')

    def test_rejected_after_deadline_to_apply(self):
        task = TaskFactory.create(status='open', people_needed=2, type='event')
        member = TaskMemberFactory.create(task=task, status='accepted', externals=1)

        self.assertEqual(task.status, 'full')
        task.deadline_to_apply = timezone.now() - timedelta(days=1)

        member.status = 'rejected'
        member.save()

        self.assertEqual(task.status, 'full')

    def test_task_realized(self):
        task = TaskFactory.create(status='open', people_needed=2, type='event')
        TaskMemberFactory.create(task=task, status='accepted', externals=1)

        self.assertEqual(task.status, 'full')

        task.deadline = timezone.now() - timedelta(days=1)
        task.deadline_reached()

        self.assertEqual(task.status, 'realized')

    def test_task_only_applied(self):
        task = TaskFactory.create(status='open', people_needed=2, type='event')
        TaskMemberFactory.create(task=task, status='applied')

        self.assertEqual(task.status, 'open')

        task.deadline = timezone.now() - timedelta(days=1)
        task.deadline_reached()

        self.assertEqual(task.status, 'closed')

    def test_task_no_members(self):
        task = TaskFactory.create(status='open', people_needed=2, type='event')

        self.assertEqual(task.status, 'open')

        task.deadline = timezone.now() - timedelta(days=1)
        task.deadline_reached()

        self.assertEqual(task.status, 'closed')
        self.assertEquals(len(mail.outbox), 1)

        self.assertTrue('set to closed' in mail.outbox[0].subject)

    def test_full_after_deadline_to_apply(self):
        task = TaskFactory.create(status='open', people_needed=2, type='event')

        TaskMemberFactory.create(task=task, status='applied')
        self.assertEqual(task.status, 'open')

        task.deadline_to_apply = timezone.now() - timedelta(days=1)
        task.deadline_to_apply_reached()

        self.assertEqual(task.status, 'full')
        self.assertEqual(task.people_needed, 1)

        email = mail.outbox[-1]
        self.assertEqual(
            email.subject,
            "The deadline to apply for your task '{}' has passed".format(task.title)
        )
        self.assertTrue(
            "The task has been set to 'full' with the {} candidates that applied".format(
                task.people_applied) in email.body
        )
        self.assertTrue(
            'Edit task https://testserver/tasks/{}/edit'.format(task.id) in email.body
        )

    def test_ongoing_running_after_deadline_to_apply(self):
        task = TaskFactory.create(status='open', people_needed=2, type='ongoing')

        TaskMemberFactory.create(task=task, status='applied')
        self.assertEqual(task.status, 'open')

        task.deadline_to_apply = timezone.now() - timedelta(days=1)
        task.deadline_to_apply_reached()

        self.assertEqual(task.status, 'in progress')
        self.assertEqual(task.people_needed, 1)

        email = mail.outbox[-1]
        self.assertEqual(
            email.subject,
            "The deadline to apply for your task '{}' has passed".format(task.title)
        )
        self.assertTrue(
            "The task has been set to 'running' with the {} candidates that applied".format(
                task.people_applied) in email.body
        )
        self.assertTrue(
            'Edit task https://testserver/tasks/{}/edit'.format(task.id) in email.body
        )

    def test_ongoing_running_after_deadline_to_apply_to_many(self):
        task = TaskFactory.create(status='open', people_needed=2, type='ongoing')

        TaskMemberFactory.create(task=task, status='applied', externals=2)
        self.assertEqual(task.status, 'open')

        task.deadline_to_apply = timezone.now() - timedelta(days=1)
        task.deadline_to_apply_reached()

        self.assertEqual(task.status, 'in progress')
        self.assertEqual(task.people_needed, 2)

        email = mail.outbox[-1]
        self.assertEqual(
            email.subject,
            "The deadline to apply for your task '{}' has passed".format(task.title)
        )
        self.assertTrue(
            "Your task has been set to 'running'" in email.body
        )
        self.assertTrue(
            "You still have to accept your candidates" in email.body
        )

        self.assertTrue(
            'Accept candidates: https://testserver/tasks/{}'.format(task.id) in email.body
        )

    def test_event_running_after_deadline_to_apply_to_many(self):
        task = TaskFactory.create(status='open', people_needed=2, type='event')

        TaskMemberFactory.create(task=task, status='applied', externals=2)
        self.assertEqual(task.status, 'open')

        task.deadline_to_apply = timezone.now() - timedelta(days=1)
        task.deadline_to_apply_reached()

        self.assertEqual(task.status, 'full')
        self.assertEqual(task.people_needed, 2)

        email = mail.outbox[-1]
        self.assertEqual(
            email.subject,
            "The deadline to apply for your task '{}' has passed".format(task.title)
        )
        self.assertTrue(
            "Your task has been set to 'full'" in email.body
        )
        self.assertTrue(
            "You still have to accept your candidates" in email.body
        )

        self.assertTrue(
            'Accept candidates: https://testserver/tasks/{}'.format(task.id) in email.body
        )

    def test_ongoing_running_accepted_running_after_deadline_to_apply(self):
        task = TaskFactory.create(status='open', people_needed=2, type='ongoing')

        TaskMemberFactory.create(task=task, status='accepted', externals=2)

        task.deadline_to_apply = timezone.now() - timedelta(days=1)
        task.deadline_to_apply_reached()

        self.assertEqual(task.status, 'in progress')
        self.assertEqual(task.people_needed, 2)

        email = mail.outbox[-1]
        self.assertEqual(
            email.subject,
            "The deadline to apply for your task '{}' has passed".format(task.title)
        )
        self.assertTrue(
            "The task has been set to 'running'" in email.body
        )
        self.assertTrue(
            "Leave a message" in email.body
        )

    def test_event_running_accepted_running_after_deadline_to_apply(self):
        task = TaskFactory.create(status='open', people_needed=2, type='event')

        TaskMemberFactory.create(task=task, status='accepted', externals=2)

        task.deadline_to_apply = timezone.now() - timedelta(days=1)
        task.deadline_to_apply_reached()

        self.assertEqual(task.status, 'full')
        self.assertEqual(task.people_needed, 2)

        email = mail.outbox[-1]
        self.assertEqual(
            email.subject,
            "The deadline to apply for your task '{}' has passed".format(task.title)
        )
        self.assertTrue(
            "The task has been set to 'full'" in email.body
        )
        self.assertTrue(
            "Leave a message" in email.body
        )

    def test_no_members_after_deadline_to_apply(self):
        task = TaskFactory.create(status='open', people_needed=2, type='ongoing')

        self.assertEqual(task.status, 'open')

        task.deadline_to_apply = timezone.now() - timedelta(days=1)
        task.deadline_to_apply_reached()

        self.assertEqual(task.status, 'closed')
        self.assertEqual(task.people_needed, 2)

        email = mail.outbox[-1]
        self.assertEqual(
            email.subject,
            "The deadline to apply for your task '{}' has passed".format(task.title)
        )

        self.assertTrue(
            "the task is set to 'closed'" in email.body
        )
        self.assertTrue(
            'Edit task https://testserver/tasks/{}/edit'.format(task.id) in email.body
        )

    def test_no_members_after_deadline_to_apply_withdrew(self):
        task = TaskFactory.create(status='open', people_needed=2, type='ongoing')

        self.assertEqual(task.status, 'open')

        member = TaskMemberFactory.create(task=task, status='accepted', externals=0)
        member.delete()

        task.deadline_to_apply = timezone.now() - timedelta(days=1)
        task.deadline_to_apply_reached()

        self.assertEqual(task.status, 'closed')
        self.assertEqual(task.people_needed, 2)

        email = mail.outbox[-1]
        self.assertEqual(
            email.subject,
            "The deadline to apply for your task '{}' has passed".format(task.title)
        )

        self.assertTrue(
            "the task is set to 'closed'" in email.body
        )
        self.assertTrue(
            'Edit task https://testserver/tasks/{}/edit'.format(task.id) in email.body
        )

    def test_task_member_realized(self):
        task = TaskFactory.create(status='open', people_needed=2, type='ongoing')
        member = TaskMemberFactory.create(task=task, status='applied')

        self.assertEqual(task.status, 'open')

        task.deadline = timezone.now() - timedelta(days=1)
        task.deadline_reached()

        self.assertEqual(task.status, 'closed')

        member.status = 'realized'
        member.save()

        self.assertEqual(task.status, 'realized')

    def test_task_member_realized_to_rejected(self):
        task = TaskFactory.create(status='realized', people_needed=2, type='ongoing')
        member = TaskMemberFactory.create(task=task, status='realized')

        self.assertEqual(task.status, 'realized')

        member.status = 'rejected'
        member.save()

        self.assertEqual(task.status, 'closed')

    def test_task_member_realized_to_partially_rejected(self):
        task = TaskFactory.create(status='realized', people_needed=2, type='ongoing')
        member = TaskMemberFactory.create(task=task, status='realized')
        TaskMemberFactory.create(task=task, status='realized')

        self.assertEqual(task.status, 'realized')

        member.status = 'rejected'
        member.save()

        self.assertEqual(task.status, 'realized')

    def test_task_member_applied_to_realized(self):
        task = TaskFactory.create(status='open', people_needed=2, type='ongoing')
        member = TaskMemberFactory.create(task=task, status='applied')
        TaskMemberFactory.create(task=task, status='applied')

        task.deadline_reached()

        self.assertEqual(task.status, 'closed')

        member.status = 'realized'
        member.save()

        self.assertEqual(task.status, 'realized')


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
