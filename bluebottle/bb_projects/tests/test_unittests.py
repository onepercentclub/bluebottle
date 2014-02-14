from django.test import TestCase
from bluebottle.test.factory_models.projects import ProjectFactory
from bluebottle.bb_projects.tests import TestBaseProject

class TestProjectTestCase(TestCase):
    def setUp(self):
            pass

    def test_fake(self):
        self.assertEquals(TestBaseProject.objects.count(), 0)
        project = ProjectFactory.create()
        self.assertEquals(TestBaseProject.objects.count(), 1)