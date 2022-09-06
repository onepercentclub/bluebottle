import datetime

from django.utils.timezone import get_current_timezone

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory
from bluebottle.time_based.utils import duplicate_slot


tz = get_current_timezone()


class DuplicateSlotTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        self.activity = DateActivityFactory.create(
            slots=[]
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=tz.localize(datetime.datetime(2022, 5, 15, 10, 0)),
            status='cancelled'
        )

    def _get_slot_dates(self):
        return [str(s.start.date()) for s in self.activity.slots.all()]

    def _get_slot_statuses(self):
        return [s.status for s in self.activity.slots.all()]

    def test_duplicate_every_day(self):
        end = datetime.date(2022, 5, 20)
        duplicate_slot(self.slot, 'day', end)
        self.assertEqual(
            self._get_slot_dates(),
            [
                '2022-05-15', '2022-05-16', '2022-05-17',
                '2022-05-18', '2022-05-19', '2022-05-20',
            ]
        )
        self.assertEqual(
            self._get_slot_statuses(),
            [
                'cancelled', 'finished', 'finished',
                'finished', 'finished', 'finished'
            ]
        )

    def test_duplicate_every_day_end_dst(self):
        self.slot.start = tz.localize(datetime.datetime(2022, 10, 27, 10, 0))
        self.slot.save()

        end = datetime.date(2022, 11, 2)
        duplicate_slot(self.slot, 'day', end)

        self.assertEqual(
            self._get_slot_dates(),
            [
                '2022-10-27', '2022-10-28', '2022-10-29',
                '2022-10-30', '2022-10-31', '2022-11-01',
                '2022-11-02'
            ]
        )

        for slot in self.activity.slots.all():
            self.assertEqual(slot.start.astimezone(tz).hour, 10)
            self.assertEqual(slot.start.astimezone(tz).minute, 0)

    def test_duplicate_every_week(self):
        end = datetime.date(2022, 7, 1)
        duplicate_slot(self.slot, 'week', end)
        self.assertEqual(
            self._get_slot_dates(),
            [
                '2022-05-15', '2022-05-22', '2022-05-29',
                '2022-06-05', '2022-06-12', '2022-06-19',
                '2022-06-26',
            ]
        )

    def test_duplicate_every_monthday(self):
        end = datetime.date(2023, 2, 1)
        duplicate_slot(self.slot, 'monthday', end)
        self.assertEqual(
            self._get_slot_dates(),
            [
                '2022-05-15', '2022-06-15', '2022-07-15',
                '2022-08-15', '2022-09-15', '2022-10-15',
                '2022-11-15', '2022-12-15', '2023-01-15',
            ]
        )

    def test_duplicate_every_3rd_sunday(self):
        end = datetime.date(2022, 10, 1)
        duplicate_slot(self.slot, 'month', end)
        self.assertEqual(
            self._get_slot_dates(),
            [
                '2022-05-15', '2022-06-19', '2022-07-17',
                '2022-08-21', '2022-09-18',
            ]
        )
