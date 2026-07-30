from django.core.exceptions import MultipleObjectsReturned

from bluebottle.activity_pub.tests.factories import SubEventFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    ScheduleActivityFactory,
    ScheduleSlotFactory,
    TeamFactory,
)


class SlotOriginPropertyTestCase(BluebottleTestCase):
    def setUp(self):
        self.activity = ScheduleActivityFactory.create(team_activity='teams')
        self.team = TeamFactory.create(activity=self.activity)
        self.slot = self.team.slots.get()

    def test_single_origin_returns_origin(self):
        sub_event = SubEventFactory.create(adopted=self.slot)
        self.assertTrue(hasattr(self.slot, 'origin'))
        self.assertEqual(self.slot.origin, sub_event)

    def test_missing_origin_hides_attribute(self):
        self.assertFalse(hasattr(self.slot, 'origin'))
        with self.assertRaises(AttributeError):
            _ = self.slot.origin

    def test_multiple_origins_returns_first(self):
        first = SubEventFactory.create(adopted=self.slot)
        SubEventFactory.create(adopted=self.slot)

        try:
            origin = self.slot.origin
        except MultipleObjectsReturned:
            self.fail('Slot.origin raised MultipleObjectsReturned')

        self.assertEqual(origin, first)
        self.assertEqual(self.slot.origins.count(), 2)


class ScheduleSlotOriginPropertyTestCase(BluebottleTestCase):
    def setUp(self):
        self.activity = ScheduleActivityFactory.create()
        self.slot = ScheduleSlotFactory.create(activity=self.activity)

    def test_missing_origin_hides_attribute(self):
        self.assertFalse(hasattr(self.slot, 'origin'))

    def test_single_origin_returns_origin(self):
        sub_event = SubEventFactory.create(adopted=self.slot)
        self.assertEqual(self.slot.origin, sub_event)
