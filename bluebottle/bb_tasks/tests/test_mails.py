from bluebottle.tasks.models import Task, TaskMember
from bluebottle.test.utils import BluebottleTestCase
from django.core import mail

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory


class TaskEmailTests(BluebottleTestCase):
    """
    Tests for tasks: sending e-mails on certain status changes.
    """

    def setUp(self):
        super(TaskEmailTests, self).setUp()
        self.init_projects()

        self.some_user = BlueBottleUserFactory.create(first_name='King',
                                                      primary_language='fr')
        self.another_user = BlueBottleUserFactory.create(first_name='Kong',
                                                         primary_language='nl')

        self.yet_another_user = BlueBottleUserFactory.create(first_name='Gong',
                                                             primary_language='en')

        self.some_project = ProjectFactory.create()
        self.some_project.owner.primary_language = 'en'

        self.task = TaskFactory.create(
            status=Task.TaskStatuses.in_progress,
            author=self.some_project.owner,
        )

        self.taskmember1 = TaskMemberFactory.create(
            member=self.some_user,
            status=TaskMember.TaskMemberStatuses.applied,
            task=self.task

        )
        self.taskmember2 = TaskMemberFactory.create(
            member=self.another_user,
            status=TaskMember.TaskMemberStatuses.applied,
            task=self.task
        )

        self.task.save()

    def test_mail_taskmember_applied_sent(self):
        """
        Test that the e-mails were sent for the task applications.
        """
        self.assertEqual(len(mail.outbox), 2)

        m = mail.outbox.pop(0)
        self.assertEqual(m.subject, 'King applied for your task')
        self.assertEqual(m.activated_language,
                         self.some_project.owner.primary_language)
        self.assertEqual(m.recipients()[0], self.some_project.owner.email)

        m = mail.outbox.pop(0)
        self.assertEqual(m.subject, 'Kong applied for your task')
        self.assertEqual(m.activated_language,
                         self.some_project.owner.primary_language)
        self.assertEqual(m.recipients()[0], self.some_project.owner.email)

    def test_mail_member_accepted(self):
        """
        Test the sent mail for accepted task members.
        """
        # there should be two mails in the outbox from the application
        self.assertEqual(len(mail.outbox), 2)
        # delete them, they're not relevant for this test
        del mail.outbox[:2]

        # change the status from one member to accepted -> he should receive
        # an e-mail
        self.taskmember1.status = TaskMember.TaskMemberStatuses.accepted
        self.taskmember1.save()

        # test that the e-mail is indeed sent
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox.pop(0)
        self.assertIn('assigned you to a task', m.subject)
        self.assertEqual(m.activated_language,
                         self.taskmember1.member.primary_language)
        self.assertEqual(m.recipients()[0], self.some_user.email)

    def test_mail_member_joined(self):
        """
        Test the sent mail for auto accepted task members.
        """
        self.task.accepting = Task.TaskAcceptingChoices.automatic
        self.task.save()

        mail.outbox = []

        taskmember = TaskMemberFactory.create(
            member=self.yet_another_user,
            status=TaskMember.TaskMemberStatuses.applied,
            task=self.task
        )

        self.assertEqual(taskmember.status, 'accepted')

        # test that the e-mail is indeed sent
        self.assertEqual(len(mail.outbox), 1)

        m = mail.outbox.pop(0)
        self.assertIn('Gong joined your task', m.subject)
        self.assertEqual(m.recipients()[0], self.some_project.owner.email)
