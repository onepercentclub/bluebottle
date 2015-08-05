from django.core import mail
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.tasks import TaskFactory, TaskMemberFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase

# import taskmail in order to properly register mail handlers. Without it tests mail fail
from bluebottle.bb_tasks import taskmail

@override_settings(SEND_WELCOME_MAIL=False)
class TestTaskMails(BluebottleTestCase):
    """
    Test the sending of email notifications when a Task' status changes
    """

    def setUp(self):
        super(TestTaskMails, self).setUp()

        self.init_projects()
        self.status_running = ProjectPhase.objects.get(slug='campaign')
        self.project = ProjectFactory.create(status=self.status_running)
        self.task = TaskFactory.create(project=self.project)

    def test_member_applied_to_task_mail(self):
        """
        Test emails for realized task with a task member
        """
        self.task.status = "in progress"
        self.assertEquals(len(mail.outbox), 0)
        self.task.save()

        self.task_member = TaskMemberFactory.create(task=self.task, status='applied')

        # Task owner receives email about new task member
        self.assertEquals(len(mail.outbox), 1)
        self.assertNotEquals(mail.outbox[0].body.find("applied for your task"), -1)
        self.assertEquals(mail.outbox[0].to[0], self.task.author.email)

        self.task_member.status = 'accepted'
        self.task_member.save()

        # Task member receives email that he is accepted
        self.assertEquals(len(mail.outbox), 2)
        self.assertNotEquals(mail.outbox[1].subject.find("assigned"), -1)
        self.assertEquals(mail.outbox[1].to[0], self.task_member.member.email)

    def test_status_realized_mail(self):
        """
        Setting status to realized should trigger email
        """
        self.task.status = "in progress"
        self.task.save()
        self.assertEquals(len(mail.outbox), 0)

        self.task.status = "realized"
        self.task.save()
        self.assertEquals(len(mail.outbox), 1)

        self.failIf(mail.outbox[0].body.find("You've set your task") == -1)

    def test_status_realized_to_ip(self):
        """
        A state change from realized to in progress should not trigger a mail
        """
        self.task.status = "realized"
        self.task.save()
        mail.outbox[:] = []

        self.task.status = "in progress"
        self.task.save()

        self.assertEquals(len(mail.outbox), 0)

    def test_expired_mail(self):
        """
        deadline_reached should send email
        """
        self.task.deadline_reached()
        self.assertEquals(len(mail.outbox), 1)
        self.failIf(mail.outbox[0].body.find("The deadline of your task") == -1)

