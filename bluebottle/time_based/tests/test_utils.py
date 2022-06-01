import datetime

from pytz import UTC

from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory
from bluebottle.time_based.utils import duplicate_slot


class DuplicateSlotTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        self.activity = DateActivityFactory.create(
            slots=[]
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=datetime.datetime(2022, 5, 15, tzinfo=UTC)
        )

    def _get_slot_dates(self):
        return [str(s.start.date()) for s in self.activity.slots.all()]

    def test_duplicate_every_day(self):
        end = datetime.datetime(2022, 5, 20, tzinfo=UTC).date()
        duplicate_slot(self.slot, 'day', end)
        self.assertEqual(
            self._get_slot_dates(),
            [
                '2022-05-15', '2022-05-16', '2022-05-17',
                '2022-05-18', '2022-05-19', '2022-05-20',
            ]
        )

    def test_duplicate_every_week(self):
        end = datetime.datetime(2022, 7, 1, tzinfo=UTC).date()
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
        end = datetime.datetime(2023, 2, 1, tzinfo=UTC).date()
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
        end = datetime.datetime(2022, 10, 1, tzinfo=UTC).date()
        duplicate_slot(self.slot, 'month', end)
        self.assertEqual(
            self._get_slot_dates(),
            [
                '2022-05-15', '2022-06-19', '2022-07-17',
                '2022-08-21', '2022-09-18',
            ]
        )
