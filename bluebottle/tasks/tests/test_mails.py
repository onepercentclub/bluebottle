from datetime import timedelta
from mock import patch

from django.db import connection
from django.core import mail
from django.test.utils import override_settings
from django.utils.timezone import now

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.tasks.taskmail import send_task_realized_mail
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
        self.task = TaskFactory.create(project=self.project)


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
        self.assertTrue(self.task_member.member.full_name in body)
        self.assertEquals(mail.outbox[0].to[0], self.task.author.email)

        self.task_member.status = 'accepted'
        self.task_member.save()

        # Task member receives email that he is accepted
        self.assertEquals(len(mail.outbox), 2)
        self.assertNotEquals(mail.outbox[1].subject.find("assigned"), -1)
        self.assertEquals(mail.outbox[1].to[0], self.task_member.member.email)

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
            status='accepted'
        )

        task_member.status = 'realized'
        task_member.save()

        self.assertEquals(len(mail.outbox), 2)

        email = mail.outbox[-1]

        self.assertNotEquals(email.subject.find("realised"), -1)
        self.assertEquals(email.to[0], task_member.member.email)

    def test_member_realized_mail_with_survey(self):
        survey = SurveyFactory(link='https://example.com/survey/1/')

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
        self.assertTrue(
            'Hopefully your task was a great success' in email.body
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

    def test_closed_mail(self):
        """
        Closing a project should send an email
        """
        self.task.status = "closed"
        self.task.save()
        self.assertEquals(len(mail.outbox), 1)

        self.assertTrue('set to closed' in mail.outbox[0].subject)
