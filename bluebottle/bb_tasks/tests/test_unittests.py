from django.test import TestCase
from bluebottle.bb_tasks import get_task_model

TASK_MODEL = get_task_model()

class TestTaskTestCase(TestCase):
    def setUp(self):
        pass

    def test_demo(self):
        self.assertEquals(TASK_MODEL.objects.count(), 0)
