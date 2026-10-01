from types import SimpleNamespace

from django.test.client import RequestFactory
from elasticsearch_dsl.utils import AttrDict

from bluebottle.activities.serializers.preview import (
    ActivityPreviewLocationSerializer,
    ActivityPreviewSlottedLocationSerializer,
)
from bluebottle.activities.serializers.serializers import ActivityPreviewSerializer
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
        return {'request': RequestFactory().get('/')}

    def test_slotted_location_uses_activity_geofeatures(self):
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(self._activity())

        self.assertEqual(location, 'Ouddorp, NL')

    def test_slotted_location_without_geofeatures_returns_none(self):
        activity = self._activity(geofeature=[])
        location = ActivityPreviewSlottedLocationSerializer(
            context=self._context(),
        ).to_representation(activity)

        self.assertIsNone(location)

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

        self.assertEqual(location, 'Netherlands')

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

    def test_full_address_primary_still_uses_city_country(self):
        activity = self._activity(
            geofeature=[
                self._geofeature(
                    'address',
                    'Brouwersdam Buitenzijde 20',
                    place_name=(
                        'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands'
                    ),
                    is_primary=True,
                ),
                self._geofeature('place', 'Ouddorp'),
                self._geofeature('country', 'Netherlands'),
            ],
        )
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(activity)

        self.assertEqual(location, 'Ouddorp, NL')

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
        serializer = ActivityPreviewLocationSerializer(context=self._context())

        self.assertEqual(serializer.to_representation(activity), 'Netherlands')
        self.assertFalse(serializer.has_multiple_unresolved_locations(activity))


class ActivityPreviewLocationWithoutCountryCodeTestCase(BluebottleTestCase):
    """Regression tests for BB-30097.

    Indexed activity documents are not guaranteed to carry every field: a
    geofeature is only given a ``country_code`` when its geolocation has a
    country, and documents indexed before a mapping change can lack the field
    altogether. Reading such a field straight off the Elasticsearch ``AttrDict``
    raised ``AttributeError: 'AttrDict' object has no attribute 'country_code'``
    and turned /api/activities/search into a 500.
    """

    def setUp(self):
        super().setUp()
        settings = InitiativePlatformSettings.load()
        settings.card_location_display = 'city_country'
        settings.save()

    def _geofeature(self, feature_type, name, **extra):
        # Deliberately no 'country_code' key: mirrors prepare_geofeature, which
        # only sets it when the geolocation has a country.
        entry = {
            'language': 'en',
            'name': name,
            'place_name': name,
            'feature_type': feature_type,
            'is_primary': False,
            'country': 'Netherlands',
        }
        entry.update(extra)
        return entry

    def _document(self, **kwargs):
        defaults = {
            'type': 'deed',
            'status': 'open',
            'location': [
                # No 'country_code' key, as in the stale BMW Group documents.
                {'id': 42, 'locality': 'Ouddorp', 'type': 'location'}
            ],
            'geofeature': [
                self._geofeature('place', 'Ouddorp'),
                self._geofeature('country', 'Netherlands'),
            ],
            'country': [],
        }
        defaults.update(kwargs)
        return AttrDict(defaults)

    def _context(self):
        return {'request': RequestFactory().get('/')}

    def test_location_without_country_code_falls_back_to_country_name(self):
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(self._document())

        self.assertEqual(location, 'Ouddorp, Netherlands')

    def test_location_without_country_code_or_country(self):
        # 'city_country' has nothing to pair the city with, so it yields no
        # label at all -- but it must not raise.
        document = self._document(
            geofeature=[
                self._geofeature('place', 'Ouddorp', country=None),
            ],
        )
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(document)

        self.assertIsNone(location)

    def test_location_entry_without_type_is_skipped(self):
        document = self._document(location=[{'id': 42, 'locality': 'Ouddorp'}])
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(document)

        self.assertIsNone(location)

    def test_slotted_location_without_country_code(self):
        document = self._document(
            type='dateactivity',
            slots=[
                {
                    'status': 'open',
                    'start': '2026-08-01T10:00:00+00:00',
                    'end': '2026-08-01T12:00:00+00:00',
                    'is_online': False,
                    'location_id': 42,
                    'geofeatures': [],
                }
            ],
        )
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(document)

        self.assertEqual(location, 'Ouddorp, Netherlands')

    def test_multiple_slot_locations_without_country_code(self):
        document = self._document(
            type='dateactivity',
            geofeature=[],
            location=[
                {'id': 1, 'locality': 'Amsterdam', 'type': 'location'},
                {'id': 2, 'locality': 'Haarlem', 'type': 'location'},
            ],
            slots=[
                {
                    'status': 'open',
                    'start': '2026-08-01T10:00:00+00:00',
                    'end': '2026-08-01T12:00:00+00:00',
                    'is_online': False,
                    'location_id': 1,
                    'geofeatures': [
                        self._geofeature('place', 'Amsterdam'),
                        self._geofeature('region', 'North Holland'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                },
                {
                    'status': 'open',
                    'start': '2026-08-02T10:00:00+00:00',
                    'end': '2026-08-02T12:00:00+00:00',
                    'is_online': False,
                    'location_id': 2,
                    'geofeatures': [
                        self._geofeature('place', 'Haarlem'),
                        self._geofeature('region', 'North Holland'),
                        self._geofeature('country', 'Netherlands'),
                    ],
                },
            ],
        )
        location = ActivityPreviewLocationSerializer(
            context=self._context(),
        ).to_representation(document)

        self.assertEqual(location, 'North Holland, Netherlands')

    def test_preview_serializer_get_location_without_country_code(self):
        serializer = ActivityPreviewSerializer(context=self._context())

        self.assertEqual(
            serializer.get_location(self._document()), 'Ouddorp, Netherlands'
        )
