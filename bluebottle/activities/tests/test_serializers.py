from types import SimpleNamespace

from django.test.client import RequestFactory

from bluebottle.activities.serializers.preview import (
    ActivityPreviewLocationSerializer,
    ActivityPreviewSlottedLocationSerializer,
)
from bluebottle.activities.serializers.serializers import ActivityPreviewSerializer
from bluebottle.activities.utils import ResourceRolesField
from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.initiatives.models import InitiativePlatformSettings
from bluebottle.offices.tests.factories import LocationFactory, OfficeSubRegionFactory
from bluebottle.segments.tests.factories import SegmentFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
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


class ResourceRolesFieldTestCase(BluebottleTestCase):
    def setUp(self):
        super().setUp()
        self.activity = DeedFactory.create()

    def _roles(self, user):
        request = RequestFactory().get('/')
        request.user = user
        field = ResourceRolesField()
        field._context = {'request': request}
        return field.to_representation(self.activity)

    def test_other_user_has_no_roles(self):
        self.assertEqual(
            self._roles(BlueBottleUserFactory.create()),
            {'manager': False, 'reviewer': False},
        )

    def test_owner_is_manager(self):
        self.assertEqual(
            self._roles(self.activity.owner),
            {'manager': True, 'reviewer': False},
        )

    def test_activity_manager_is_manager(self):
        manager = BlueBottleUserFactory.create()
        self.activity.initiative.activity_managers.add(manager)

        self.assertEqual(
            self._roles(manager),
            {'manager': True, 'reviewer': False},
        )

    def test_staff_is_reviewer(self):
        staff = BlueBottleUserFactory.create(is_staff=True)

        self.assertEqual(
            self._roles(staff),
            {'manager': False, 'reviewer': True},
        )

    def test_superuser_is_reviewer(self):
        superuser = BlueBottleUserFactory.create(is_superuser=True)

        self.assertEqual(
            self._roles(superuser),
            {'manager': False, 'reviewer': True},
        )

    def test_staff_subregion_manager_only_reviews_matching_region(self):
        managed = OfficeSubRegionFactory.create()
        other = OfficeSubRegionFactory.create()
        staff = BlueBottleUserFactory.create(is_staff=True)
        staff.subregion_manager.add(managed)
        self.activity.office_location = LocationFactory.create(subregion=other)
        self.activity.save()

        self.assertFalse(self._roles(staff)['reviewer'])

        self.activity.office_location = LocationFactory.create(subregion=managed)
        self.activity.save()

        self.assertTrue(self._roles(staff)['reviewer'])

    def test_staff_segment_manager_only_reviews_matching_segment(self):
        managed = SegmentFactory.create()
        other = SegmentFactory.create()
        staff = BlueBottleUserFactory.create(is_staff=True)
        staff.segment_manager.add(managed)
        self.activity.segments.add(other)

        self.assertFalse(self._roles(staff)['reviewer'])

        self.activity.segments.add(managed)

        self.assertTrue(self._roles(staff)['reviewer'])
