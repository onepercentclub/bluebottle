from django.test import TestCase

from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.time_based.tests.factories import PeriodActivityFactory
from bluebottle.impact.tests.factories import ImpactGoalFactory


class ImpactGoalModelTestCase(TestCase):
    def setUp(self):
        self.model = ImpactGoalFactory.create(activity=DeedFactory.create(), target=None)

        super(ImpactGoalModelTestCase, self).setUp()

    def test_required_deed(self):
        self.assertEqual(list(self.model.required), ['target'])

    def test_required_period(self):
        self.model.activity = PeriodActivityFactory.create()
        self.assertEqual(list(self.model.required), [])
