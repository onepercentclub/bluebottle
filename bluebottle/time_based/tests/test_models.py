from datetime import timedelta

from django.utils.timezone import now

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory


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
