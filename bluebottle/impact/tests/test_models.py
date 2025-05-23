from django.test import TestCase

from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.impact.tests.factories import ImpactGoalFactory


class ImpactGoalModelTestCase(TestCase):
    def setUp(self):
        self.model = ImpactGoalFactory.create(activity=DeedFactory.create(), target=None)

        super(ImpactGoalModelTestCase, self).setUp()

    def test_required_deed(self):
        self.assertEqual(list(self.model.required), ['target'])
