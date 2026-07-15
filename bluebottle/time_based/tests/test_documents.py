from bluebottle.test.geo_utils import ensure_geolocation_geofeatures
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.documents import (
    DateActivityDocument,
    deduplicate_locations,
    deduplicate_positions,
    unique_slot_geolocations,
)
from bluebottle.time_based.tests.factories import DateActivityFactory, DateActivitySlotFactory


class DateActivityDocumentTestCase(BluebottleTestCase):
    def create_geolocation(self, **kwargs):
        geolocation = GeolocationFactory.build(**kwargs)
        if geolocation.country_id is None and geolocation.country:
            geolocation.country.save()
        geolocation.save(skip_mapbox_sync=True)
        return geolocation

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

    def test_prepare_geofeature_deduplicates_by_unique_slot_locations(self):
        location = self.create_geolocation(locality='Leiden')
        activity = DateActivityFactory.create(slots=[])
        DateActivitySlotFactory.create(activity=activity, location=location)
        DateActivitySlotFactory.create(activity=activity, location=location)

        document = DateActivityDocument()
        geofeatures = document.prepare_geofeature(activity)

        self.assertEqual(geofeatures, [])

    def test_prepare_slots_includes_per_slot_geofeatures(self):
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
        self.assertGreater(len(slots[0]['geofeatures']), 0)

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
