from bluebottle.bb_projects.tests.testproject.models import TestBaseProject
from bluebottle.bb_projects.tests.testproject.test import BaseProjectTestCase
from bluebottle.test.factory_models.projects import ProjectFactory

class BaseProjectTests(BaseProjectTestCase):
    """
    Demo TestCase for the abstract base project class
    """
    def test_demo_test(self):
        self.assertEquals(TestBaseProject.objects.all().count(), 0)
        obj = ProjectFactory.create()
        self.assertEquals(TestBaseProject.objects.all().count(), 1)

        model_fields = ['country', 'created', 'description', 'favorite', u'id', 'image', 'owner',
                        'pitch', 'slug', 'status', 'theme', 'updated', 'title']
        self.assertEquals(cmp(model_fields, obj._meta.get_all_field_names()), 1)