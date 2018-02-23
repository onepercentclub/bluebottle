from datetime import timedelta
from mock import patch

from django.db import connection
from django.core import mail
from django.core.management import call_command
from django.test.utils import override_settings
from django.utils.timezone import now

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.models import TaskMember
from bluebottle.tasks.taskmail import send_task_realized_mail
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.surveys import SurveyFactory
from bluebottle.test.utils import BluebottleTestCase

# import taskmail in order to properly register mail handlers. Without it tests mail fail
from bluebottle.tasks import taskmail  # noqa


@override_settings(SEND_WELCOME_MAIL=False)
class TaskMailTestBase(BluebottleTestCase):
    """
    Test the sending of email notifications when a Task' status changes
    """

    def setUp(self):
        super(TaskMailTestBase, self).setUp()

        self.init_projects()
        self.status_running = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(status=self.status_running)
        self.task = TaskFactory.create(project=self.project, deadline=now() + timedelta(days=2))


class TestTaskMemberMail(TaskMailTestBase):
    def test_member_applied_to_task_mail(self):
        """
        Test emails for realized task with a task member
        """
        self.task.status = "in progress"
        self.assertEquals(len(mail.outbox), 0)
        self.task.save()

        self.task_member = TaskMemberFactory.create(task=self.task,
                                                    status='applied')

        # Task owner receives email about new task member
        self.assertEquals(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertTrue('applied for your task' in body)
        self.assertFalse('with the following motivation' in body)
        self.assertTrue(self.task_member.member.full_name in body)
        self.assertEquals(mail.outbox[0].to[0], self.task.author.email)

        self.task_member.status = 'accepted'
        self.task_member.save()

        # Task member receives email that he is accepted
        self.assertEquals(len(mail.outbox), 2)
        self.assertNotEquals(mail.outbox[1].subject.find("assigned"), -1)
        self.assertEquals(mail.outbox[1].to[0], self.task_member.member.email)
        self.assertTrue(
            'Hi {}'.format(self.task_member.member.short_name) in mail.outbox[1].body
        )
        self.assertTrue(
            'initiator, {}'.format(self.task.author.short_name) in mail.outbox[1].body
        )

    def test_member_applied_to_task_mail_not_to_project_owner(self):
        """
        Test emails for realized task with a task member
        """
        self.project.owner = BlueBottleUserFactory()
        self.project.save()

        self.task.status = "in progress"
        self.assertEquals(len(mail.outbox), 0)
        self.task.save()

        self.task_member = TaskMemberFactory.create(task=self.task,
                                                    status='applied')

        # Task owner receives email about new task member
        self.assertEquals(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertTrue('applied for your task' in body)
        self.assertFalse('with the following motivation' in body)
        self.assertTrue(self.task_member.member.full_name in body)
        self.assertEquals(mail.outbox[0].to[0], self.task.author.email)

        self.task_member.status = 'accepted'
        self.task_member.save()

        # Task member receives email that he is accepted
        self.assertEquals(len(mail.outbox), 2)
        self.assertNotEquals(mail.outbox[1].subject.find("assigned"), -1)
        self.assertEquals(mail.outbox[1].to[0], self.task_member.member.email)

    def test_member_applied_with_motivation_to_task_mail(self):
        """
        Test emails for realized task with a task member
        """
        self.task.status = "in progress"
        self.assertEquals(len(mail.outbox), 0)
        self.task.save()

        self.task_member = TaskMemberFactory.create(
            task=self.task,
            motivation='Some motivation',
            status='applied'
        )

        # Task owner receives email about new task member
        self.assertEquals(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertTrue('applied for your task' in body)
        self.assertTrue('with the following motivation' in body)
        self.assertTrue('Some motivation' in body)

    def test_member_withdrew_to_task_mail(self):
        """
        Test emails for realized task with a task member
        """
        self.task_member = TaskMemberFactory.create(task=self.task,
                                                    status='withdrew')

        # Task owner receives email about new task member
        self.assertEquals(len(mail.outbox), 1)
        body = mail.outbox[0].body
        self.assertTrue('withdrew from the task' in body)
        self.assertTrue(self.task_member.member.full_name in body)
        self.assertEquals(mail.outbox[0].to[0], self.task.author.email)

    def test_member_realized_mail(self):
        task_member = TaskMemberFactory.create(
            task=self.task,
            status='accepted',
            time_spent=8
        )

        task_member.status = 'realized'
        task_member.save()

        self.assertEquals(len(mail.outbox), 2)

        email = mail.outbox[-1]

        self.assertNotEquals(email.subject.find("realised"), -1)
        self.assertTrue('spent {} hours'.format(task_member.time_spent) in email.body)
        self.assertEquals(email.to[0], task_member.member.email)

    def test_member_realized_mail_with_survey(self):
        survey = SurveyFactory(link='https://example.com/survey/1/', active=True)

        task_member = TaskMemberFactory.create(
            task=self.task,
            status='accepted'
        )

        task_member.status = 'realized'
        task_member.save()

        self.assertEquals(len(mail.outbox), 2)

        email = mail.outbox[-1]

        self.assertNotEquals(email.subject.find("realised"), -1)
        self.assertEquals(email.to[0], task_member.member.email)
        self.assertTrue(survey.url(self.task) in email.body)
        self.assertTrue('survey' in email.body)

    def test_member_realized_mail_with_inactive_survey(self):
        SurveyFactory(link='https://example.com/survey/1/', active=False)

        task_member = TaskMemberFactory.create(
            task=self.task,
            status='accepted'
        )

        task_member.status = 'realized'
        task_member.save()

        self.assertEquals(len(mail.outbox), 2)

        email = mail.outbox[-1]

        self.assertNotEquals(email.subject.find("realised"), -1)
        self.assertEquals(email.to[0], task_member.member.email)
        self.assertFalse('survey' in email.body)

    def test_member_realized_mail_not_sent_twice(self):
        task_member = TaskMemberFactory.create(
            task=self.task,
            status='accepted'
        )

        task_member.status = 'realized'
        task_member.save()

        self.assertEquals(len(mail.outbox), 2)

        # Make sure we reload the member, so that _original_status is correct
        task_member = TaskMember.objects.get(pk=task_member.pk)
        task_member.time_spent = 4
        task_member.save()

        self.assertEquals(len(mail.outbox), 2)


@override_settings(CELERY_RESULT_BACKEND='amqp')
class TestTaskStatusMail(TaskMailTestBase):
    def test_status_realized_mail(self):
        """
        Setting status to realized should trigger email
        """
        self.task.status = "in progress"
        self.task.save()
        self.assertEquals(len(mail.outbox), 0)

        with patch('bluebottle.tasks.taskmail.send_task_realized_mail.apply_async') as mock_task:
            self.task.status = "realized"
            self.task.save()

        # There should be one email send immediately
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue('set to realized' in mail.outbox[0].subject)
        self.assertTrue('Hello {}'.format(self.task.author.short_name) in mail.outbox[0].body)

        # And there should be 2 scheduled

        # One in 3 days
        (args1, kwargs1), (args2, kwargs2) = mock_task.call_args_list
        self.assertEqual(args1[0][0], self.task)
        self.assertEqual(args1[0][1], 'task_status_realized_reminder')
        self.assertTrue(
            now() + timedelta(days=3) - kwargs1['eta'] < timedelta(minutes=1)
        )

        # and one in 6 days
        self.assertEqual(args2[0][0], self.task)
        self.assertEqual(args2[0][1], 'task_status_realized_second_reminder')
        self.assertTrue(
            now() + timedelta(days=6) - kwargs2['eta'] < timedelta(minutes=1)
        )

    @override_settings(REMINDER_MAIL_DELAY=60)
    def test_status_realized_mail_override_delay(self):
        """
        Setting status to realized should trigger email
        """
        self.task.status = "in progress"
        self.task.save()
        self.assertEquals(len(mail.outbox), 0)

        with patch('bluebottle.tasks.taskmail.send_task_realized_mail.apply_async') as mock_task:
            self.task.status = "realized"
            self.task.save()

        # One mail should be scheduled in 60 minutes
        (args1, kwargs1), (args2, kwargs2) = mock_task.call_args_list
        self.assertTrue(
            now() + timedelta(minutes=60) - kwargs1['eta'] < timedelta(minutes=1)
        )

        # and one in 120 minutes
        self.assertTrue(
            now() + timedelta(minutes=120) - kwargs2['eta'] < timedelta(minutes=1)
        )

    def test_status_realized_mail_already_confirmed(self):
        """
        Setting status to realized should trigger no email if there is already somebody realized
        """
        self.task.status = "in progress"
        self.task.save()
        self.assertEquals(len(mail.outbox), 0)

        self.task_member = TaskMemberFactory.create(
            task=self.task,
            status='realized'
        )
        self.assertEquals(len(mail.outbox), 1)
        self.assertTrue('You realised a task' in mail.outbox[0].subject)

        with patch('bluebottle.tasks.taskmail.send_task_realized_mail.apply_async'):
            self.task.status = "realized"
            self.task.save()

        self.assertEquals(len(mail.outbox), 1)

    def test_status_realized_reminder(self):
        send_task_realized_mail(
            self.task,
            'task_status_realized_reminder',
            'test subject',
            connection.tenant
        )

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'test subject')
        self.assertTrue('Hello {}'.format(self.task.author.short_name) in mail.outbox[0].body)
        self.assertTrue(
            'Hopefully your task "{}" was a great success'.format(self.task.title) in email.body
        )
        self.assertTrue(
            'https://testserver/go/tasks/{}'.format(self.task.pk) in email.body
        )

    def test_status_realized_second_reminder(self):
        send_task_realized_mail(
            self.task,
            'task_status_realized_second_reminder',
            'test subject',
            connection.tenant
        )

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'test subject')
        self.assertTrue(
            'In case it slipped your mind' in email.body
        )
        self.assertTrue('Hello {}'.format(self.task.author.short_name) in mail.outbox[0].body)
        self.assertTrue(
            'https://testserver/go/tasks/{}'.format(self.task.pk) in email.body
        )

    def test_status_realized_to_ip(self):
        """
        A state change from realized to in progress should not trigger a mail
        """
        with patch('bluebottle.tasks.taskmail.send_task_realized_mail.apply_async'):
            self.task.status = "realized"
            self.task.save()

        mail.outbox[:] = []

        self.task.status = "in progress"
        self.task.save()

        self.assertEquals(len(mail.outbox), 0)


class TestDeadlineChangedEmail(TaskMailTestBase):
    def setUp(self):
        super(TestDeadlineChangedEmail, self).setUp()
        self.task_members = TaskMemberFactory.create_batch(4, task=self.task, status='applied')
        mail.outbox = []

    def test_deadline_changed_email(self):
        """
        Changing the deadline should trigger an email
        """
        self.task.deadline = now() + timedelta(days=4)
        self.task.save()

        # There should be 4 emails send
        self.assertEquals(len(mail.outbox), 4)
        self.assertTrue('deadline' in mail.outbox[0].subject)

    def test_deadline_changed_withdrew(self):
        self.task_members[0].status = 'withdrew'
        self.task_members[0].save()

        mail.outbox = []

        self.task.deadline = now() + timedelta(days=4)
        self.task.save()

        # There should be 3 emails send
        self.assertEquals(len(mail.outbox), 3)
        self.assertTrue('deadline' in mail.outbox[0].subject)


class TestDeadlineToApplyEmail(TaskMailTestBase):
    def setUp(self):
        super(TestDeadlineToApplyEmail, self).setUp()

        self.task.deadline = now() + timedelta(days=4)
        self.task.deadline_to_apply = now()
        self.task.people_needed = 10
        self.task.type = 'event'
        self.task.status = 'open'
        self.task.save()

    def test_deadline_to_apply_reached_event_target_reached_email(self):
        """
        Event task with enough people.
        Run status realised cron job should send mails and change task status.
        """
        TaskMemberFactory.create_batch(10, task=self.task, status='accepted')
        self.assertEquals(len(mail.outbox), 10)

        call_command('cron_status_realised')
        self.assertEquals(len(mail.outbox), 11)
        self.assertEquals(self.task.status, 'full')

        # running the status realised cron job should not send an new email
        call_command('cron_status_realised')
        self.assertEquals(len(mail.outbox), 11)

    def test_deadline_to_apply_reached_event_target_not_reached_email(self):
        """
        Event task without enough people.
        Run status realised cron job should send mails and change task status.
        """
        TaskMemberFactory.create_batch(4, task=self.task, status='accepted')
        self.assertEquals(len(mail.outbox), 4)

        call_command('cron_status_realised')
        self.assertEquals(len(mail.outbox), 5)
        self.assertEquals(self.task.status, 'open')

        # running the status realised cron job should not send an new email
        call_command('cron_status_realised')
        self.assertEquals(len(mail.outbox), 5)

    def test_deadline_to_apply_reached_ongoing_target_reached_email(self):
        """
        Ongoing task with enough people.
        Run status realised cron job should send mails and change task status.
        """
        self.task.type = 'ongoing'
        self.task.save()
        TaskMemberFactory.create_batch(10, task=self.task, status='accepted')
        self.assertEquals(len(mail.outbox), 10)

        call_command('cron_status_realised')
        self.assertEquals(len(mail.outbox), 11)
        self.assertEquals(self.task.status, 'in progress')

        # running the status realised cron job should not send an new email
        call_command('cron_status_realised')
        self.assertEquals(len(mail.outbox), 11)

    def test_deadline_to_apply_reached_ongoing_target_not_reached_email(self):
        """
        Ongoing task with enough people.
        Run status realised cron job should send mails and change task status.
        """
        self.task.type = 'ongoing'
        self.task.save()
        TaskMemberFactory.create_batch(4, task=self.task, status='accepted')
        self.assertEquals(len(mail.outbox), 4)

        call_command('cron_status_realised')
        self.assertEquals(len(mail.outbox), 5)
        self.assertEquals(self.task.status, 'open')

        # running the status realised cron job should not send an new email
        call_command('cron_status_realised')
        self.assertEquals(len(mail.outbox), 5)
