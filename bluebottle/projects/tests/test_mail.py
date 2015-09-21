from django.core import mail
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.utils import BluebottleTestCase


@override_settings(SEND_WELCOME_MAIL=False)
class TestProjectMails(BluebottleTestCase):
    """
    Test the sending of email notifications when a Task' status changes
    """

    def setUp(self):
        super(TestProjectMails, self).setUp()

        self.init_projects()
        self.status_running = ProjectPhase.objects.get(slug='campaign')
        self.complete = ProjectPhase.objects.get(slug='done-complete')
        self.incomplete = ProjectPhase.objects.get(slug='done-incomplete')
        self.project = ProjectFactory.create(status=self.status_running)

    def test_complete(self):
        self.project.status = self.complete
        self.project.save()

        self.assertEquals(len(mail.outbox), 1)
        self.assertNotEquals(mail.outbox[0].subject.find("has been realised"), -1)

    def test_incomplete(self):
        self.project.status = self.incomplete
        self.project.save()

        self.assertEquals(len(mail.outbox), 1)
        self.assertNotEquals(mail.outbox[0].subject.find("has expired"), -1)

    def test_state_other(self):
        self.project.status = ProjectPhase.objects.get(slug="plan-new")
        self.project.save()

        self.assertEquals(len(mail.outbox), 0)

        self.project.status = ProjectPhase.objects.get(slug="closed")
        self.project.save()

        self.assertEquals(len(mail.outbox), 0)
