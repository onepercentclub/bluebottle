from bluebottle.funding.documents import FundingDocument
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.geo.mapbox import locality_from_geolocation
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.geo_utils import ensure_geolocation_geofeatures, save_built_geolocation
from bluebottle.test.utils import BluebottleTestCase


class FundingDocumentTestCase(BluebottleTestCase):
    def create_geolocation(self, **kwargs):
        return save_built_geolocation(GeolocationFactory.build(**kwargs))

    def test_prepare_location_impact_location_without_country(self):
        impact_location = self.create_geolocation(
            country=None,
            locality='Amsterdam',
            formatted_address='Dam 1, Amsterdam',
        )
        ensure_geolocation_geofeatures(impact_location)
        funding = FundingFactory.create(impact_location=impact_location)

        document = FundingDocument()
        locations = document.prepare_location(funding)

        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0]['id'], impact_location.id)
        self.assertEqual(locations[0]['name'], impact_location.geofeature.place_name)
        self.assertEqual(
            locations[0]['locality'],
            locality_from_geolocation(impact_location),
        )
        self.assertIsNone(locations[0]['country_code'])
        self.assertIsNone(locations[0]['country'])
        self.assertEqual(locations[0]['type'], 'location')

    def test_prepare_location_uses_initiative_place_without_impact_location(self):
        funding = FundingFactory.create(impact_location=None)

        document = FundingDocument()
        locations = document.prepare_location(funding)

        place = funding.initiative.place
        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0]['id'], place.id)
        self.assertEqual(
            locations[0]['locality'],
            locality_from_geolocation(place),
        )
        self.assertEqual(locations[0]['country_code'], place.country.alpha2_code)
        self.assertEqual(locations[0]['type'], 'impact_location')

    def test_prepare_indexing_impact_location_without_country(self):
        impact_location = self.create_geolocation(
            country=None,
            locality='Amsterdam',
            formatted_address='Dam 1, Amsterdam',
        )
        ensure_geolocation_geofeatures(impact_location)
        funding = FundingFactory.create(impact_location=impact_location)

        prepared = FundingDocument().prepare(funding)

        self.assertEqual(
            prepared['location'],
            [{
                'id': impact_location.id,
                'name': impact_location.geofeature.place_name,
                'locality': locality_from_geolocation(impact_location),
                'country_code': None,
                'country': None,
                'type': 'location',
            }],
        )
