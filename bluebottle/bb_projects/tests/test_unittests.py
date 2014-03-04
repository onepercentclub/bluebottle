from django.test import TestCase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.utils.utils import get_project_model

PROJECT_MODEL = get_project_model()

class TestProjectTestCase(TestCase):
    def setUp(self):
            pass

    def test_fake(self):
        self.assertEquals(PROJECT_MODEL.objects.count(), 0)
        project = ProjectFactory.create()
        self.assertEquals(PROJECT_MODEL.objects.count(), 1)