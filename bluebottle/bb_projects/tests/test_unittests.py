from bluebottle.test.utils import BluebottleTestCase
from bluebottle.test.factory_models.projects import ProjectFactory, ProjectPhaseFactory
from bluebottle.utils.model_dispatcher import get_project_model, get_project_phaselog_model

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


