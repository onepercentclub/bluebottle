from django.core import mail
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.surveys.models import Survey
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.factory_models.surveys import SurveyFactory
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
        self.project = ProjectFactory.create(status=self.status_running, organization=None)
        self.survey = SurveyFactory(link='https://example.com/survey/1/')

    def test_complete(self):
        self.project.status = self.complete
        self.project.save()

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertNotEquals(email.subject.find("has been realised"), -1)

        self.assertTrue(self.survey.url(self.project, user_type='initiator') in email.body)

    def test_complete_no_celebration(self):
        self.project.celebrate_results = False
        self.project.status = self.complete
        self.project.save()

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]

        self.assertNotEquals(email.subject.find("has been realised"), -1)
        self.assertFalse('survey' in email.body)

    def test_complete_with_organization(self):
        self.project.organization = OrganizationFactory.create(email='organization@example.com')
        self.project.status = self.complete
        self.project.save()

        self.assertEquals(len(mail.outbox), 2)
        initiator_email = mail.outbox[0]
        self.assertEqual(initiator_email.to, [self.project.owner.email])
        self.assertTrue('has been realised' in initiator_email.subject)
        self.assertTrue(Survey.url(self.project, user_type='initiator') in initiator_email.body)

        organization_email = mail.outbox[1]
        self.assertEqual(organization_email.to, [self.project.organization.email])
        self.assertTrue('has been realised' in organization_email.subject)
        self.assertTrue(Survey.url(self.project, user_type='organization') in organization_email.body)

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


@override_settings(SEND_WELCOME_MAIL=False)
class TestProjectRoleMails(BluebottleTestCase):
    """
    Test the sending of email to project initiator, promoter and task manager
    """

    def setUp(self):
        super(TestProjectRoleMails, self).setUp()

        self.init_projects()
        self.project = ProjectFactory.create()
        self.user = BlueBottleUserFactory.create()

    def test_manager(self):
        self.project.task_manager = self.user
        self.project.save()
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertTrue('Task manager' in str(email.subject))
        self.assertTrue(self.project.title in str(email.subject))
        self.assertTrue(self.user.email in email.recipients())
        self.assertTrue(self.user.short_name in email.body)
        self.assertTrue('/projects/{}'.format(self.project.slug) in email.body)
        self.assertTrue('Task manager' in email.body)
        self.assertTrue(self.project.title in email.body)

    def test_reviewer(self):
        self.project.reviewer = self.user
        self.project.save()
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertTrue('Project reviewer' in str(email.subject))
        self.assertTrue(self.project.title in str(email.subject))
        self.assertTrue(self.user.email in email.recipients())
        self.assertTrue(self.user.short_name in email.body)
        self.assertTrue(
            reverse('admin:projects_project_change', args=(self.project.pk, )) in email.body
        )
        self.assertTrue('Project reviewer' in email.body)
        self.assertTrue(self.project.title in email.body)

    def test_promoter(self):
        self.project.promoter = self.user
        self.project.save()
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        self.assertTrue('Project promoter' in str(email.subject))
        self.assertTrue(self.project.title in str(email.subject))
        self.assertTrue(self.user.email in email.recipients())
        self.assertTrue(self.user.short_name in email.body)
        self.assertTrue('/projects/{}'.format(self.project.slug) in email.body)
        self.assertTrue('Project promoter' in email.body)
        self.assertTrue(self.project.title in email.body)

    def test_set_twice(self):
        self.project.promoter = self.user
        self.project.save()
        self.project.promoter = self.user
        self.project.save()

        self.assertEqual(len(mail.outbox), 1)

    def test_multiple(self):
        self.project.promoter = self.user
        self.project.task_manager = self.user
        self.project.reviewer = self.user
        self.project.save()

        self.assertEqual(len(mail.outbox), 3)
