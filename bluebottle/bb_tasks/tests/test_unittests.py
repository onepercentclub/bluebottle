from bluebottle.bb_tasks.tests import TestTask
from django.test import TestCase

class TestTaskTestCase(TestCase):
    def setUp(self):
        pass

    def test_demo(self):
        self.assertEquals(TestTask.objects.count(), 0)
