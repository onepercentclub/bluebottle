from datetime import timedelta

from django.utils.timezone import now

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory, DateActivitySlotFactory, PeriodActivityFactory
)


class DeadlineActivityModelTestCase(BluebottleTestCase):
    def test_registrion_deadline_validation_empty(self):
        activity = PeriodActivityFactory.create(
            start=None,
            deadline=None,
            registration_deadline=None
        )

        self.assertEqual(list(activity.errors), [])

    def test_registrion_deadline_validation_no_start_or_deadline(self):
        activity = PeriodActivityFactory.create(
            start=None,
            deadline=None,
            registration_deadline=now() + timedelta(days=10)
        )

        self.assertEqual(list(activity.errors), [])

    def test_registrion_deadline_validation_after_deadline(self):
        activity = PeriodActivityFactory.create(
            start=None,
            deadline=now() + timedelta(days=5),
            registration_deadline=now() + timedelta(days=10)
        )

        self.assertEqual(len(list(activity.errors)), 1)
        self.assertEqual(list(activity.errors)[0].field, 'registration_deadline')

    def test_registrion_deadline_validation_before_both(self):
        activity = PeriodActivityFactory.create(
            start=now() + timedelta(days=10),
            deadline=now() + timedelta(days=10),
            registration_deadline=now() + timedelta(days=5)
        )

        self.assertEqual(list(activity.errors), [])


class DateActivityModelTestCase(BluebottleTestCase):

    def setUp(self):
        self.activity = DateActivityFactory.create(
            slots=[]
        )
        self.slotA = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() + timedelta(days=10)
        )
        self.slotB = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() + timedelta(days=3)
        )
        self.slotC = DateActivitySlotFactory.create(
            activity=self.activity,
            start=now() + timedelta(days=4)
        )
        self.slotD = DateActivitySlotFactory.create(
            activity=self.activity,
            start=None
        )

    def test_slot_sequence(self):
        self.assertEqual(self.slotA.sequence, 3)
        self.assertEqual(self.slotB.sequence, 1)
        self.assertEqual(self.slotC.sequence, 2)
        self.assertEqual(self.slotD.sequence, 4)

        self.assertEqual(str(self.slotA), 'Slot 3')
        self.assertEqual(str(self.slotB), 'Slot 1')
        self.assertEqual(str(self.slotC), 'Slot 2')
        self.assertEqual(str(self.slotD), 'Slot 4')

    def test_slot_sequence_change_dates(self):
        self.slotD.start = now() + timedelta(days=8)
        self.slotD.save()
        self.assertEqual(self.slotA.sequence, 4)
        self.assertEqual(self.slotB.sequence, 1)
        self.assertEqual(self.slotC.sequence, 2)
        self.assertEqual(self.slotD.sequence, 3)
