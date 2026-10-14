
import datetime

from django.contrib.gis.geos import Point
from django.utils.timezone import get_current_timezone, make_aware
from pytz import utc

from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DeadlineActivityFactory,
    ScheduleSlotFactory,
)
from bluebottle.time_based.utils import (
    duplicate_slot,
    duration_to_hours,
    get_local_time_help_text,
    get_slot_local_datetimes,
)
from bluebottle.time_based.views.exports import format_slot_start_for_export


tz = get_current_timezone()
AMSTERDAM = Point(4.9041, 52.3676)
NEW_YORK = Point(-74.006, 40.7128)


class DuplicateSlotTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        self.activity = DateActivityFactory.create(
            slots=[]
        )
        self.slot = DateActivitySlotFactory.create(
            activity=self.activity,
            start=make_aware(datetime.datetime(2022, 5, 15, 10, 0), tz),
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
        self.slot.start = make_aware(datetime.datetime(2022, 10, 27, 10, 0), tz)
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


class TestDurationToHours(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.activity = DeadlineActivityFactory.create(
            duration=datetime.timedelta(hours=12)
        )

    def test_hours(self):
        self.assertEqual(
            duration_to_hours(self.activity.duration), 12
        )

    def test_half_hours(self):
        self.activity.duration = datetime.timedelta(hours=12, minutes=40)
        self.assertEqual(
            duration_to_hours(self.activity.duration), 13
        )

    def test_more_then_day(self):
        self.activity.duration = datetime.timedelta(days=1, hours=18)
        self.assertEqual(
            duration_to_hours(self.activity.duration), 42
        )


class GetSlotLocalDatetimesTestCase(BluebottleTestCase):
    def _utc_start(self, year, month, day, hour=8, minute=30):
        return datetime.datetime(year, month, day, hour, minute, tzinfo=utc)

    def test_on_site_platform_timezone(self):
        slot = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            location=GeolocationFactory.create(position=AMSTERDAM),
            is_online=False,
        )
        start, end, is_local = get_slot_local_datetimes(slot)
        self.assertEqual(start.hour, 9)
        self.assertEqual(start.minute, 30)
        self.assertFalse(is_local)
        self.assertIsNotNone(end)

    def test_on_site_foreign_timezone(self):
        slot = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            location=GeolocationFactory.create(position=NEW_YORK),
            is_online=False,
        )
        start, end, is_local = get_slot_local_datetimes(slot)
        self.assertEqual(start.hour, 3)
        self.assertEqual(start.minute, 30)
        self.assertTrue(is_local)

    def test_online(self):
        slot = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            location=None,
            is_online=True,
        )
        start, end, is_local = get_slot_local_datetimes(slot)
        self.assertEqual(start.hour, 9)
        self.assertEqual(start.minute, 30)
        self.assertFalse(is_local)

    def test_no_location(self):
        slot = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            location=None,
            is_online=False,
        )
        start, end, is_local = get_slot_local_datetimes(slot)
        self.assertEqual(start.hour, 9)
        self.assertEqual(start.minute, 30)
        self.assertFalse(is_local)

    def test_no_start(self):
        slot = ScheduleSlotFactory.create(start=None, duration=None)
        self.assertEqual(get_slot_local_datetimes(slot), (None, None, False))

    def test_no_duration(self):
        slot = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            duration=None,
            is_online=True,
            location=None,
        )
        start, end, is_local = get_slot_local_datetimes(slot)
        self.assertEqual(start.hour, 9)
        self.assertIsNone(end)
        self.assertFalse(is_local)

    def test_winter_and_summer(self):
        winter = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            location=None,
            is_online=True,
        )
        summer = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 7, 5),
            location=None,
            is_online=True,
        )
        winter_start, _, _ = get_slot_local_datetimes(winter)
        summer_start, _, _ = get_slot_local_datetimes(summer)
        self.assertEqual(winter_start.hour, 9)
        self.assertEqual(summer_start.hour, 10)

    def test_help_text_foreign_timezone(self):
        slot = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            location=GeolocationFactory.create(position=NEW_YORK),
            is_online=False,
        )
        help_text = get_local_time_help_text(slot)
        self.assertIsNotNone(help_text)
        self.assertIn('3:30', help_text)
        self.assertNotIn('1.0 hours', help_text)
        self.assertIn('Europe/Amsterdam', help_text)

    def test_help_text_online(self):
        slot = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            location=None,
            is_online=True,
        )
        self.assertIsNone(get_local_time_help_text(slot))

    def test_export_start_uses_platform_timezone(self):
        slot = ScheduleSlotFactory.create(
            start=self._utc_start(2025, 11, 5),
            location=None,
            is_online=True,
        )
        self.assertEqual(format_slot_start_for_export(slot), '05-11-25 09:30')
