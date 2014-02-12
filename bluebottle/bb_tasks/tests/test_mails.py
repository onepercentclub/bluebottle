from django.core import mail
from django.test import TestCase

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory

from bluebottle.bb_tasks import get_task_model
from bluebottle.bb_tasks.models import TaskMember

BB_TASK_MODEL = get_task_model()


class TaskEmailTests(TestCase):
    """ Tests for tasks: sending e-mails on certain status changes. """

    def setUp(self):
        self.some_user = BlueBottleUserFactory.create(first_name='King')
        self.another_user = BlueBottleUserFactory.create(first_name='Kong')

        self.some_project = ProjectFactory.create()
        self.task = TaskFactory(
            status = BB_TASK_MODEL.TaskStatuses.in_progress,
            author = self.some_project.owner
            )

        self.taskmember1 = TaskMemberFactory(
                member = self.some_user,
                task = self.task,
                status = TaskMember.TaskMemberStatuses.applied
            )
        self.taskmember2 = TaskMemberFactory(
                member = self.another_user,
                task = self.task,
                status = TaskMember.TaskMemberStatuses.applied
            )

    def test_mail_taskmember_applied_sent(self):
        """ Test that the e-mails were sent for the task applications """
        self.assertEqual(len(mail.outbox), 2)

        m = mail.outbox.pop(0)
        self.assertEqual(m.subject, 'King applied for your task.')
        self.assertEqual(m.recipients()[0], self.some_project.owner.email)

        m = mail.outbox.pop(0)
        self.assertEqual(m.subject, 'Kong applied for your task.')
        self.assertEqual(m.recipients()[0], self.some_project.owner.email)

    def test_mails_task_realized_and_mail_rejected(self):
        """
        Test that the task members receive an e-mail when the task changes status to realized.

        As 'collateral' the test for the taskmember-rejected e-mail is contained in this test.
        """

        # there should be two mails in the outbox from the application
        self.assertEqual(len(mail.outbox), 2)
        # delete them, they're not relevant for this test
        del mail.outbox[:2]
        # sanity check
        self.assertEqual(len(mail.outbox), 0)

        # change the status from one member to rejected -> he shouldn't get the e-mail
        self.taskmember1.status = TaskMember.TaskMemberStatuses.rejected
        self.taskmember1.save()

        # e-mail should be sent to inform of rejection
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox.pop()
        self.assertIn('found someone else to do the task you applied for.', m.subject)

        # change the status from the task to realized
        self.task.status = BB_TASK_MODEL.TaskStatuses.realized
        self.task.save()

        # e-mails should be outbound by now, to the single taskmember left
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox.pop()
        subject = '"{0}" is realized'.format(self.task.title)
        self.assertIn(subject, m.subject)

    def test_mail_member_accepted(self):
        """ Test the sent mail for accepted task members """

        # there should be two mails in the outbox from the application
        self.assertEqual(len(mail.outbox), 2)
        # delete them, they're not relevant for this test
        del mail.outbox[:2]

        # change the status from one member to accepted -> he should receive an e-mail
        self.taskmember1.status = TaskMember.TaskMemberStatuses.accepted
        self.taskmember1.save()

        # test that the e-mail is indeed sent
        self.assertEqual(len(mail.outbox), 1)
        m = mail.outbox.pop(0)
        self.assertIn('accepted you to complete the tasks you applied for.', m.subject)
        self.assertEqual(m.recipients()[0], self.some_user.email)
