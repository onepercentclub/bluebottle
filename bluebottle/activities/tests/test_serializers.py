from types import SimpleNamespace
from unittest.mock import MagicMock

from bluebottle.activities.preview_serializers import (
    ActivityPreviewLocationSerializer,
    ActivityPreviewSlottedLocationSerializer,
    ActivityPreviewSlotSelection,
)
from bluebottle.activities.serializers import ActivityPreviewSerializer
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.test.utils import BluebottleTestCase


class ActivityPreviewLocationTestCase(BluebottleTestCase):

    def setUp(self):
        super().setUp()
        settings = InitiativePlatformSettings.load()
        settings.card_location_display = 'city_country'
        settings.save()

    def _slot(self, **kwargs):
        defaults = {
            'status': 'open',
            'start': '2026-08-01T10:00:00+00:00',
            'end': '2026-08-01T12:00:00+00:00',
            'locality': 'Brouwersdam Buitenzijde 20',
            'formatted_address': (
                'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands'
            ),
            'country': 'Netherlands',
            'country_code': 'NL',
            'is_online': False,
            'location_id': 42,
            'geofeatures': [],
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def _activity(self, **kwargs):
        defaults = {
            'type': 'dateactivity',
            'status': 'open',
            'slots': [self._slot()],
            'location': [
                SimpleNamespace(
                    id=42,
                    locality='Ouddorp',
                    country='Netherlands',
                    country_code='NL',
                    type='location',
                )
            ],
            'geofeature': [
                SimpleNamespace(
                    id=1,
                    name='Ouddorp',
                    place_name='Ouddorp, Netherlands',
                    language='en',
                    feature_type='place',
                    is_primary=False,
                    country='Netherlands',
                    country_code='NL',
                ),
                SimpleNamespace(
                    id=2,
                    name='Netherlands',
                    place_name='Netherlands',
                    language='en',
                    feature_type='country',
                    is_primary=False,
                    country='Netherlands',
                    country_code='NL',
                ),
            ],
            'country': [],
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def _context(self):
        return {'request': MagicMock(GET={})}

    def test_slotted_location_uses_activity_geofeatures(self):
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(self._activity())

        self.assertEqual(location, 'Ouddorp, NL')

    def test_slotted_location_fallback_uses_indexed_city_not_address(self):
        activity = self._activity(geofeature=[])
        location = ActivityPreviewSlottedLocationSerializer(
            context=self._context(),
        ).to_representation(activity)

        self.assertEqual(location, 'Ouddorp, NL')

    def test_multiple_slot_localities_return_none(self):
        activity = self._activity(slots=[
            self._slot(locality='Amsterdam'),
            self._slot(locality='Rotterdam'),
        ])
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(activity)

        self.assertIsNone(location)

    def test_preview_serializer_delegates_to_location_serializer(self):
        serializer = ActivityPreviewSerializer(context=self._context())
        location = serializer.get_location(self._activity())

        self.assertEqual(location, 'Ouddorp, NL')

    def test_slot_selection_for_card(self):
        activity = self._activity(slots=[
            self._slot(locality='Amsterdam'),
            self._slot(locality='Rotterdam'),
        ])
        slots = ActivityPreviewSlotSelection(
            activity, MagicMock(GET={})
        ).for_card()

        self.assertEqual(len({slot.locality for slot in slots}), 2)
