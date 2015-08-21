from django.utils import timezone
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.bb_projects.models import ProjectPhase
from bluebottle.projects.models import Project
from bluebottle.test.factory_models.donations import DonationFactory
from bluebottle.test.factory_models.orders import OrderFactory
from bluebottle.test.factory_models.projects import (ProjectFactory,
                                                     ProjectPhaseFactory)
from bluebottle.utils.model_dispatcher import (get_project_model,
                                               get_project_phaselog_model)

PROJECT_MODEL = get_project_model()
PROJECT_PHASE_LOG_MODEL = get_project_phaselog_model()


class TestProjectTestCase(BluebottleTestCase):
    def setUp(self):
        super(TestProjectTestCase, self).setUp()
        self.init_projects()

    def test_fake(self):
        self.assertEquals(PROJECT_MODEL.objects.count(), 0)
        project = ProjectFactory.create()
        self.assertEquals(PROJECT_MODEL.objects.count(), 1)


class TestProjectPhaseLog(TestProjectTestCase):
    def test_create_phase_log(self):
        phase1 = ProjectPhaseFactory.create()
        phase2 = ProjectPhaseFactory.create()

        project = ProjectFactory.create(status=phase1)

        phase_logs = PROJECT_PHASE_LOG_MODEL.objects.all()
        self.assertEquals(len(phase_logs), 1)
        self.assertEquals(phase_logs[0].status, project.status)

        project.status = phase2
        project.save()

        phase_logs = PROJECT_PHASE_LOG_MODEL.objects.all().order_by("-start")
        self.assertEquals(len(phase_logs), 2)
        self.assertEquals(phase_logs[0].status, project.status)


class TestProjectDonationsStatusChanges(BluebottleTestCase):
    def setUp(self):
        super(TestProjectDonationsStatusChanges, self).setUp()
        self.init_projects()

    def test_status_overfunded_projects(self):
        """ Overfunded projects should have status 'done-complete' """
        project = ProjectFactory.create(title='test', amount_asked=100)
        project.status = ProjectPhase.objects.get(slug='campaign')
        project.save()

        order = OrderFactory.create()

        donation = DonationFactory.create(
            project=project,
            order=order,
            amount=110
        )

        donation.save()

        order.locked()
        order.succeeded()
        order.save()

        project = Project.objects.get(title='test')
        project.deadline = timezone.now() - timezone.timedelta(days=1)
        project.save()

        project = Project.objects.get(title='test')
        self.assertEqual(project.status,
                         ProjectPhase.objects.get(slug='done-complete'))
