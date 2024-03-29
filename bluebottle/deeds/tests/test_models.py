from django.test import TestCase

from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.impact.tests.factories import ImpactGoalFactory


class DeedModelTestCase(TestCase):
    def setUp(self):

        self.model = DeedFactory.create(target=None)

        super(DeedModelTestCase, self).setUp()

    def test_required(self):
        self.assertEqual(list(self.model.required), [])

    def test_required_with_impact(self):
        self.model.enable_impact = True
        self.model.save()

        self.assertEqual(list(self.model.required), ['goals', 'target'])

    def test_required_with_impact_target_and_goal(self):
        self.model.enable_impact = True
        self.model.target = 100
        self.model.save()

        ImpactGoalFactory.create(activity=self.model)

        self.assertEqual(list(self.model.required), [])
