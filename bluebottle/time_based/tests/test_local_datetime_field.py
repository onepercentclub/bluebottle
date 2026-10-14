from datetime import datetime

from django.contrib.gis.geos import Point
from django.forms import ModelForm
from pytz import utc

from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.fields import (
    LocalDateTimeModelFormMixin,
    get_local_time_caption,
    localize_datetime,
    slot_timezone,
    wall_clock_to_utc,
)
from bluebottle.time_based.models import ScheduleSlot
from bluebottle.time_based.tests.factories import ScheduleSlotFactory


AMSTERDAM = Point(4.9041, 52.3676)
NEW_YORK = Point(-74.006, 40.7128)


class ScheduleSlotLocalDateTimeForm(LocalDateTimeModelFormMixin, ModelForm):
    class Meta:
        model = ScheduleSlot
        fields = ('start', 'location', 'is_online', 'duration', 'activity')


class LocalDateTimeFieldTestCase(BluebottleTestCase):
    def test_slot_timezone_online(self):
        slot = ScheduleSlotFactory.create(is_online=True, location=None)
        self.assertIsNone(slot_timezone(slot))

    def test_slot_timezone_with_location(self):
        slot = ScheduleSlotFactory.create(
            is_online=False,
            location=GeolocationFactory.create(position=NEW_YORK),
        )
        self.assertEqual(slot_timezone(slot), 'America/New_York')

    def test_localize_and_wall_clock_roundtrip(self):
        location = GeolocationFactory.create(position=NEW_YORK)
        utc_start = datetime(2025, 11, 5, 8, 30, tzinfo=utc)
        local = localize_datetime(utc_start, False, location)
        self.assertEqual(local.hour, 3)
        self.assertEqual(local.minute, 30)

        naive = local.replace(tzinfo=None)
        back = wall_clock_to_utc(naive, False, location)
        self.assertEqual(back, utc_start)

    def test_caption_always_when_location(self):
        slot = ScheduleSlotFactory.create(
            start=datetime(2025, 11, 5, 8, 30, tzinfo=utc),
            is_online=False,
            location=GeolocationFactory.create(position=AMSTERDAM),
        )
        caption = get_local_time_caption(slot)
        self.assertIn('Local time at location', str(caption))
        self.assertNotIn('in your timezone', str(caption))

    def test_caption_with_offset(self):
        slot = ScheduleSlotFactory.create(
            start=datetime(2025, 11, 5, 8, 30, tzinfo=utc),
            is_online=False,
            location=GeolocationFactory.create(position=NEW_YORK),
        )
        caption = str(get_local_time_caption(slot))
        self.assertIn('Local time at location', caption)
        self.assertIn('in your timezone (Europe/Amsterdam)', caption)

    def test_form_preserves_wall_clock_when_location_changes(self):
        amsterdam = GeolocationFactory.create(position=AMSTERDAM)
        new_york = GeolocationFactory.create(position=NEW_YORK)
        slot = ScheduleSlotFactory.create(
            start=datetime(2025, 11, 5, 8, 30, tzinfo=utc),
            is_online=False,
            location=amsterdam,
        )

        form = ScheduleSlotLocalDateTimeForm(
            data={
                'start_0': '2025-11-05',
                'start_1': '09:30:00',
                'location': new_york.pk,
                'is_online': False,
                'duration': '02:00:00',
                'activity': slot.activity_id,
            },
            instance=slot,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        local = localize_datetime(saved.start, False, new_york)
        self.assertEqual(local.hour, 9)
        self.assertEqual(local.minute, 30)
        self.assertEqual(saved.start, datetime(2025, 11, 5, 14, 30, tzinfo=utc))

    def test_form_online_uses_platform_timezone(self):
        slot = ScheduleSlotFactory.create(
            start=datetime(2025, 11, 5, 8, 30, tzinfo=utc),
            is_online=True,
            location=None,
        )
        form = ScheduleSlotLocalDateTimeForm(
            data={
                'start_0': '2025-11-05',
                'start_1': '09:30:00',
                'location': '',
                'is_online': True,
                'duration': '02:00:00',
                'activity': slot.activity_id,
            },
            instance=slot,
        )
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.start, datetime(2025, 11, 5, 8, 30, tzinfo=utc))
