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

    def _geofeature(self, feature_type, name, **extra):
        defaults = {
            'language': 'en',
            'name': name,
            'place_name': name,
            'feature_type': feature_type,
            'is_primary': False,
            'country': 'Netherlands',
            'country_code': 'NL',
        }
        defaults.update(extra)
        return SimpleNamespace(**defaults)

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
                self._geofeature('place', 'Ouddorp'),
                self._geofeature('country', 'Netherlands'),
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

    def test_multiple_slot_locations_use_common_country(self):
        activity = self._activity(
            slots=[
                self._slot(
                    location_id=1,
                    locality='Amsterdam',
                    geofeatures=[
                        self._geofeature('place', 'Amsterdam'),
                        self._geofeature('region', 'North Holland'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
                self._slot(
                    location_id=2,
                    locality='Rotterdam',
                    geofeatures=[
                        self._geofeature('place', 'Rotterdam'),
                        self._geofeature('region', 'South Holland'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
            ],
            location=[
                SimpleNamespace(
                    id=1,
                    locality='Amsterdam',
                    country='Netherlands',
                    country_code='NL',
                    type='location',
                ),
                SimpleNamespace(
                    id=2,
                    locality='Rotterdam',
                    country='Netherlands',
                    country_code='NL',
                    type='location',
                ),
            ],
            geofeature=[],
        )
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(activity)

        self.assertEqual(location, 'NL')

    def test_neighbourhood_city_multiple_locations_uses_locality_city(self):
        settings = InitiativePlatformSettings.load()
        settings.card_location_display = 'neighbourhood_city'
        settings.save()

        activity = self._activity(
            slots=[
                self._slot(
                    location_id=1,
                    geofeatures=[
                        self._geofeature('neighborhood', 'Centrum'),
                        self._geofeature('locality', 'Utrecht-Centrum'),
                        self._geofeature('place', 'Utrecht'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
                self._slot(
                    location_id=2,
                    geofeatures=[
                        self._geofeature('neighborhood', 'Lombok'),
                        self._geofeature('locality', 'Utrecht-Centrum'),
                        self._geofeature('place', 'Utrecht'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
            ],
            geofeature=[],
        )
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(activity)

        self.assertEqual(location, 'Utrecht-Centrum, Utrecht')

    def test_neighbourhood_city_multiple_locations_uses_common_city(self):
        settings = InitiativePlatformSettings.load()
        settings.card_location_display = 'neighbourhood_city'
        settings.save()

        activity = self._activity(
            slots=[
                self._slot(
                    location_id=1,
                    geofeatures=[
                        self._geofeature('neighborhood', 'Scheveningen'),
                        self._geofeature('place', 'The Hague'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
                self._slot(
                    location_id=2,
                    geofeatures=[
                        self._geofeature('neighborhood', 'Centrum'),
                        self._geofeature('place', 'The Hague'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
            ],
            geofeature=[],
        )
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(activity)

        self.assertEqual(location, 'The Hague')

    def test_city_country_multiple_cities_uses_region_country(self):
        settings = InitiativePlatformSettings.load()
        settings.card_location_display = 'city_country'
        settings.save()

        activity = self._activity(
            slots=[
                self._slot(
                    location_id=1,
                    geofeatures=[
                        self._geofeature('place', 'Amsterdam'),
                        self._geofeature('region', 'North Holland'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
                self._slot(
                    location_id=2,
                    geofeatures=[
                        self._geofeature('place', 'Haarlem'),
                        self._geofeature('region', 'North Holland'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
            ],
            geofeature=[],
        )
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(activity)

        self.assertEqual(location, 'North Holland, NL')

    def test_multiple_slot_locations_without_common_feature_return_none(self):
        activity = self._activity(
            slots=[
                self._slot(
                    location_id=1,
                    locality='Amsterdam',
                    country='Netherlands',
                    country_code='NL',
                    geofeatures=[
                        self._geofeature('place', 'Amsterdam'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
                self._slot(
                    location_id=2,
                    locality='Berlin',
                    country='Germany',
                    country_code='DE',
                    geofeatures=[
                        self._geofeature(
                            'place', 'Berlin', country='Germany', country_code='DE'
                        ),
                        self._geofeature(
                            'country', 'Germany', country='Germany', country_code='DE'
                        ),
                    ],
                ),
            ],
            geofeature=[],
        )
        serializer = ActivityPreviewLocationSerializer(context=self._context())

        self.assertIsNone(serializer.to_representation(activity))
        self.assertTrue(serializer.has_multiple_unresolved_locations(activity))

    def test_preview_serializer_delegates_to_location_serializer(self):
        serializer = ActivityPreviewSerializer(context=self._context())
        location = serializer.get_location(self._activity())

        self.assertEqual(location, 'Ouddorp, NL')

    def test_common_country_sets_has_multiple_locations_false(self):
        activity = self._activity(
            slots=[
                self._slot(
                    location_id=1,
                    geofeatures=[
                        self._geofeature('place', 'Amsterdam'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
                self._slot(
                    location_id=2,
                    geofeatures=[
                        self._geofeature('place', 'Rotterdam'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                ),
            ],
            geofeature=[],
        )
        serializer = ActivityPreviewSerializer(context=self._context())

        self.assertEqual(serializer.get_location(activity), 'NL')
        self.assertFalse(serializer.get_has_multiple_locations(activity))

    def test_slot_selection_distinct_location_ids(self):
        activity = self._activity(slots=[
            self._slot(location_id=1, locality='Amsterdam'),
            self._slot(location_id=2, locality='Rotterdam'),
        ])
        selection = ActivityPreviewSlotSelection(activity, MagicMock(GET={}))

        self.assertEqual(selection.distinct_location_ids(), {1, 2})
