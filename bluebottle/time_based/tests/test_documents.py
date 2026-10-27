from datetime import timedelta

from django.contrib.gis.geos import Point
from django.test import tag
from django.urls import reverse
from django.utils.timezone import now

from bluebottle.test.elasticsearch import ElasticsearchTestCase
from bluebottle.test.geo_utils import ensure_geolocation_geofeatures, save_built_geolocation
from bluebottle.test.factory_models.geo import GeolocationFactory, PlaceFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.documents import (
    DateActivityDocument,
    DeadlineActivityDocument,
    deduplicate_locations,
    deduplicate_positions,
    unique_slot_geolocations,
)
from bluebottle.time_based.tests.factories import (
    DateActivityFactory,
    DateActivitySlotFactory,
    DeadlineActivityFactory,
)


class DateActivityDocumentTestCase(BluebottleTestCase):
    def create_geolocation(self, **kwargs):
        return save_built_geolocation(GeolocationFactory.build(**kwargs))

    def test_unique_slot_geolocations_deduplicates_by_location(self):
        location = self.create_geolocation(locality='Leiden')
        activity = DateActivityFactory.create(slots=[])
        DateActivitySlotFactory.create(activity=activity, location=location)
        DateActivitySlotFactory.create(activity=activity, location=location)

        geolocations = unique_slot_geolocations(activity.slots.all())

        self.assertEqual(len(geolocations), 1)
        self.assertEqual(geolocations[0].id, location.id)

    def test_prepare_location_deduplicates_slot_locations(self):
        location = self.create_geolocation(locality='Leiden', formatted_address='Leiden, NL')
        ensure_geolocation_geofeatures(location)
        activity = DateActivityFactory.create(slots=[])
        DateActivitySlotFactory.create(activity=activity, location=location)
        DateActivitySlotFactory.create(activity=activity, location=location)

        document = DateActivityDocument()
        locations = document.prepare_location(activity)

        slot_locations = [
            entry for entry in locations
            if entry.get('id') == location.id and entry.get('locality') == 'Leiden'
        ]
        self.assertEqual(len(slot_locations), 1)
        self.assertEqual(slot_locations[0]['id'], location.id)

    def test_prepare_geofeature_left_empty_to_avoid_nested_duplication(self):
        location = self.create_geolocation(locality='Leiden')
        ensure_geolocation_geofeatures(location)
        activity = DateActivityFactory.create(slots=[])
        DateActivitySlotFactory.create(activity=activity, location=location)
        DateActivitySlotFactory.create(activity=activity, location=location)

        document = DateActivityDocument()
        self.assertEqual(document.prepare_geofeature(activity), [])

        locations = document.prepare_location(activity)
        slot_locations = [
            entry for entry in locations
            if entry.get('id') == location.id
        ]
        self.assertEqual(len(slot_locations), 1)
        self.assertGreater(len(slot_locations[0]['geofeatures']), 0)

    def test_prepare_slots_omits_geofeatures(self):
        location = self.create_geolocation(locality='Leiden')
        ensure_geolocation_geofeatures(location)
        activity = DateActivityFactory.create(slots=[])
        slot = DateActivitySlotFactory.create(
            activity=activity,
            location=location,
            status='open',
        )

        document = DateActivityDocument()
        slots = document.prepare_slots(activity)

        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]['id'], str(slot.pk))
        self.assertEqual(slots[0]['location_id'], location.id)
        self.assertEqual(slots[0]['locality'], 'Leiden')
        self.assertNotIn('geofeatures', slots[0])

    def test_prepare_position_deduplicates_coordinates(self):
        location = self.create_geolocation(locality='Leiden')
        activity = DateActivityFactory.create(slots=[])
        DateActivitySlotFactory.create(activity=activity, location=location)
        DateActivitySlotFactory.create(activity=activity, location=location)

        document = DateActivityDocument()
        positions = document.prepare_position(activity)

        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['lat'], location.position.y)
        self.assertEqual(positions[0]['lon'], location.position.x)

    def test_deduplicate_locations_by_id(self):
        locations = [
            {'id': 1, 'locality': 'Leiden', 'type': 'location'},
            {'id': 1, 'locality': 'Leiden', 'type': 'location'},
            {'id': 2, 'locality': 'Amsterdam', 'type': 'location'},
        ]

        self.assertEqual(len(deduplicate_locations(locations)), 2)

    def test_deduplicate_positions(self):
        positions = [
            {'lat': 52.16, 'lon': 4.49},
            {'lat': 52.16, 'lon': 4.49},
            {'lat': 52.37, 'lon': 4.89},
        ]

        self.assertEqual(len(deduplicate_positions(positions)), 2)

    def test_prepare_country_uses_unique_slot_locations(self):
        location = self.create_geolocation(locality='Leiden')
        activity = DateActivityFactory.create(slots=[])
        DateActivitySlotFactory.create(activity=activity, location=location)
        DateActivitySlotFactory.create(activity=activity, location=location)

        document = DateActivityDocument()
        countries = document.prepare_country(activity)

        country_codes = {entry['code'] for entry in countries if entry.get('code')}
        if location.country:
            self.assertEqual(len([code for code in country_codes if code == location.country.alpha2_code]), 1)


class GeolocationRelatedInstancesTestCase(BluebottleTestCase):
    def test_date_activity_found_through_slot_location(self):
        location = save_built_geolocation(GeolocationFactory.build())
        activity = DateActivityFactory.create(slots=[])
        DateActivitySlotFactory.create(activity=activity, location=location)
        DateActivitySlotFactory.create(activity=activity, location=location)
        DateActivityFactory.create()

        related = DateActivityDocument().get_instances_from_related(location)

        self.assertEqual(list(related), [activity])

    def test_deadline_activity_found_through_location(self):
        activity = DeadlineActivityFactory.create()
        DeadlineActivityFactory.create()

        related = DeadlineActivityDocument().get_instances_from_related(activity.location)

        self.assertEqual(list(related), [activity])

    def test_unused_location_matches_nothing(self):
        location = save_built_geolocation(GeolocationFactory.build())
        DateActivityFactory.create()
        DeadlineActivityFactory.create()

        self.assertEqual(list(DateActivityDocument().get_instances_from_related(location)), [])
        self.assertEqual(list(DeadlineActivityDocument().get_instances_from_related(location)), [])


@tag('elasticsearch')
class GeolocationChangeSearchTestCase(ElasticsearchTestCase):
    def search_near(self, place):
        response = self.client.get(
            reverse('activity-preview-list') +
            f'?filter[distance]=10km&filter[is_online]=0&place={place.pk}',
            HTTP_ACCEPT_LANGUAGE='en'
        )
        return [item['id'] for item in response.json()['data']]

    def test_slot_location_geocoded_after_indexing(self):
        utrecht = PlaceFactory.create(position=Point(5.12, 52.09))
        location = save_built_geolocation(GeolocationFactory.build(position=None))
        activity = DateActivityFactory.create(status='open', slots=[])
        DateActivitySlotFactory.create(
            activity=activity, status='open', is_online=False, location=location,
            start=now() + timedelta(days=10)
        )
        self.assertNotIn(str(activity.pk), self.search_near(utrecht))

        location.position = Point(5.12, 52.09)
        location.save(skip_mapbox_sync=True)

        self.assertIn(str(activity.pk), self.search_near(utrecht))

    def test_activity_location_moved(self):
        utrecht = PlaceFactory.create(position=Point(5.12, 52.09))
        activity = DeadlineActivityFactory.create(
            status='open', is_online=False,
            location=save_built_geolocation(GeolocationFactory.build(position=Point(4.9, 52.37)))
        )
        self.assertNotIn(str(activity.pk), self.search_near(utrecht))

        activity.location.position = Point(5.12, 52.09)
        activity.location.save(skip_mapbox_sync=True)

        self.assertIn(str(activity.pk), self.search_near(utrecht))
