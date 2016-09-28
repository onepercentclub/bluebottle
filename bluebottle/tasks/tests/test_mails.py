from django.core import mail
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
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
        self.assertNotEquals(mail.outbox[0].body.find("applied for your task"),
                             -1)
        self.assertEquals(mail.outbox[0].to[0], self.task.author.email)

        self.task_member.status = 'accepted'
        self.task_member.save()

        # Task member receives email that he is accepted
        self.assertEquals(len(mail.outbox), 2)
        self.assertNotEquals(mail.outbox[1].subject.find("assigned"), -1)
        self.assertEquals(mail.outbox[1].to[0], self.task_member.member.email)

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


class TestTaskStatusMail(TaskMailTestBase):
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

        self.assertTrue('set to realized' in mail.outbox[0].subject)

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

    def test_closed_mail(self):
        """
        Closing a project should send an email
        """
        self.task.status = "closed"
        self.task.save()
        self.assertEquals(len(mail.outbox), 1)

        self.assertTrue('set to closed' in mail.outbox[0].subject)

