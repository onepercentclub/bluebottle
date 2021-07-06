from datetime import timedelta

from django.utils.timezone import now
from django.contrib.auth.models import AnonymousUser

from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory
from bluebottle.time_based.serializers import DateActivityListSerializer
from bluebottle.test.utils import BluebottleTestCase

from django.test.client import RequestFactory


class DateActivityListSerializerTestCase(BluebottleTestCase):
    def setUp(self):
        self.activity = DateActivityFactory.create(slots=[])

        self.serializer = DateActivityListSerializer()
        self.request_factory = RequestFactory()

    def assertAttribute(self, attr, value, params=None):
        request = self.request_factory.get('/', params or None)
        request.user = AnonymousUser()
        request.query_params = {}
        serializer = DateActivityListSerializer(context={'request': request})
        data = serializer.to_representation(instance=self.activity)

        self.assertEqual(data[attr], value)

    def test_date_info_no_slots(self):
        self.assertAttribute('date_info', {'count': 0, 'first': None})

    def test_date_info_single_slot(self):
        slot = DateActivitySlotFactory.create(activity=self.activity)
        self.assertAttribute('date_info', {'count': 1, 'first': slot.start.date()})

    def test_date_info_multiple_dates(self):
        slots = [
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=4)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=6)),
        ]

        self.assertAttribute(
            'date_info',
            {'count': 3, 'first': min(slot.start.date() for slot in slots)}
        )

    def test_date_info_multiple_dates_overlapping(self):
        slots = [
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=6)),
        ]

        self.assertAttribute(
            'date_info',
            {'count': 2, 'first': min(slot.start.date() for slot in slots)}
        )

    def test_date_info_multiple_dates_filtered(self):
        slots = [
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=4)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=6)),
        ]

        self.assertAttribute(
            'date_info',
            {'count': 2, 'first': min(slot.start.date() for slot in slots)},
            {
                'filter[start]': (now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'filter[end]': (now() + timedelta(days=4)).strftime('%Y-%m-%d')
            }

        )

    def test_location_info_no_slots(self):
        self.assertAttribute(
            'location_info',
            {'has_multiple': False, 'is_online': False, 'location': None}
        )

    def test_location_info_single_slot(self):
        slot = DateActivitySlotFactory.create(activity=self.activity)
        self.assertAttribute(
            'location_info',
            {
                'has_multiple': False,
                'is_online': False,
                'location': '{}, {}'.format(slot.location.locality, slot.location.country.alpha2_code)
            }
        )

    def test_location_info_all_online(self):
        DateActivitySlotFactory.create(activity=self.activity, is_online=True, location=None),
        DateActivitySlotFactory.create(activity=self.activity, is_online=True, location=None),
        DateActivitySlotFactory.create(activity=self.activity, is_online=True, location=None),

        self.assertAttribute(
            'location_info',
            {'has_multiple': True, 'is_online': True, 'location': None}
        )

    def test_location_info_multiple_locations(self):
        DateActivitySlotFactory.create(activity=self.activity),
        DateActivitySlotFactory.create(activity=self.activity),
        DateActivitySlotFactory.create(activity=self.activity),

        self.assertAttribute(
            'location_info',
            {'has_multiple': True, 'is_online': False, 'location': None}
        )

    def test_location_info_multiple_dates_filtered(self):
        slots = [
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=2)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=4)),
            DateActivitySlotFactory.create(activity=self.activity, start=now() + timedelta(days=6)),
        ]

        self.assertAttribute(
            'location_info',
            {
                'has_multiple': False,
                'is_online': False,
                'location': '{}, {}'.format(
                    slots[0].location.locality, slots[0].location.country.alpha2_code
                )

            },
            {
                'filter[start]': (now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'filter[end]': (now() + timedelta(days=3)).strftime('%Y-%m-%d')
            }
        )
