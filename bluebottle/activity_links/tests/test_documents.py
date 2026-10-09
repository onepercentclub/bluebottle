from bluebottle.activity_links.documents import (
    LinkedDateActivityDocument,
    LinkedDeadlineActivityDocument,
    LinkedFundingDocument,
)
from bluebottle.activity_links.tests.factories import (
    LinkedDateActivityFactory,
    LinkedDateSlotFactory,
    LinkedDeadlineActivityFactory,
    LinkedFundingFactory,
)
from bluebottle.funding.documents import FundingDocument
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.test.factory_models.organizations import OrganizationFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.geo_utils import ensure_geolocation_geofeatures, save_built_geolocation
from bluebottle.test.utils import BluebottleTestCase
from bluebottle.time_based.documents import unique_slot_geolocations

from django.test.utils import override_settings


@override_settings(
    ELASTICSEARCH_DSL_AUTOSYNC=True,
    ELASTICSEARCH_DSL_AUTO_REFRESH=True
)
class LinkedActivityDocumentIdTestCase(BluebottleTestCase):
    def test_linked_funding_document_uses_prefixed_id(self):
        linked_funding = LinkedFundingFactory.create(host_organization=OrganizationFactory.create())
        funding = FundingFactory.create()

        linked_doc_id = LinkedFundingDocument.generate_id(linked_funding)
        funding_doc_id = FundingDocument.generate_id(funding)

        self.assertEqual(linked_doc_id, f'linked_{linked_funding.pk}')
        self.assertEqual(funding_doc_id, funding.pk)
        self.assertNotEqual(linked_doc_id, str(funding_doc_id))


class LinkedDateActivityDocumentTestCase(BluebottleTestCase):
    def create_geolocation(self, **kwargs):
        return save_built_geolocation(GeolocationFactory.build(**kwargs))

    def test_unique_slot_geolocations_deduplicates_by_location(self):
        location = self.create_geolocation(locality='Leiden')
        activity = LinkedDateActivityFactory.create()
        LinkedDateSlotFactory.create(activity=activity, location=location)
        LinkedDateSlotFactory.create(activity=activity, location=location)

        geolocations = unique_slot_geolocations(activity.slots.all())

        self.assertEqual(len(geolocations), 1)
        self.assertEqual(geolocations[0].id, location.id)

    def test_prepare_location_deduplicates_slot_locations(self):
        location = self.create_geolocation(locality='Leiden', formatted_address='Leiden, NL')
        ensure_geolocation_geofeatures(location)
        activity = LinkedDateActivityFactory.create()
        LinkedDateSlotFactory.create(activity=activity, location=location)
        LinkedDateSlotFactory.create(activity=activity, location=location)

        document = LinkedDateActivityDocument()
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
        activity = LinkedDateActivityFactory.create()
        LinkedDateSlotFactory.create(activity=activity, location=location)
        LinkedDateSlotFactory.create(activity=activity, location=location)

        document = LinkedDateActivityDocument()
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
        activity = LinkedDateActivityFactory.create()
        slot = LinkedDateSlotFactory.create(
            activity=activity,
            location=location,
        )

        document = LinkedDateActivityDocument()
        slots = document.prepare_slots(activity)

        self.assertEqual(len(slots), 1)
        self.assertEqual(slots[0]['id'], str(slot.pk))
        self.assertEqual(slots[0]['location_id'], location.id)
        self.assertEqual(slots[0]['locality'], 'Leiden')
        self.assertNotIn('geofeatures', slots[0])

    def test_prepare_position_deduplicates_coordinates(self):
        location = self.create_geolocation(locality='Leiden')
        activity = LinkedDateActivityFactory.create()
        LinkedDateSlotFactory.create(activity=activity, location=location)
        LinkedDateSlotFactory.create(activity=activity, location=location)

        document = LinkedDateActivityDocument()
        positions = document.prepare_position(activity)

        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['lat'], location.position.y)
        self.assertEqual(positions[0]['lon'], location.position.x)

    def test_prepare_country_uses_unique_slot_locations(self):
        location = self.create_geolocation(locality='Leiden')
        activity = LinkedDateActivityFactory.create()
        LinkedDateSlotFactory.create(activity=activity, location=location)
        LinkedDateSlotFactory.create(activity=activity, location=location)

        document = LinkedDateActivityDocument()
        countries = document.prepare_country(activity)

        country_codes = {entry['code'] for entry in countries if entry.get('code')}
        if location.country:
            self.assertEqual(len([code for code in country_codes if code == location.country.alpha2_code]), 1)


class LinkedDeadlineActivityDocumentTestCase(BluebottleTestCase):
    def create_geolocation(self, **kwargs):
        return save_built_geolocation(GeolocationFactory.build(**kwargs))

    def test_prepare_location_includes_geofeatures(self):
        location = self.create_geolocation(locality='Leiden')
        ensure_geolocation_geofeatures(location)
        activity = LinkedDeadlineActivityFactory.create(location=location)

        document = LinkedDeadlineActivityDocument()
        self.assertEqual(document.prepare_geofeature(activity), [])

        locations = document.prepare_location(activity)
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0]['id'], location.id)
        self.assertEqual(locations[0]['locality'], 'Leiden')
        self.assertGreater(len(locations[0]['geofeatures']), 0)
