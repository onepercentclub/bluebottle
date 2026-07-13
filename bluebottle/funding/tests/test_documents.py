from bluebottle.funding.documents import FundingDocument
from bluebottle.funding.tests.factories import FundingFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.test.utils import BluebottleTestCase


class FundingDocumentTestCase(BluebottleTestCase):
    def create_geolocation(self, **kwargs):
        geolocation = GeolocationFactory.build(**kwargs)
        geolocation.save(skip_mapbox_sync=True)
        return geolocation

    def test_prepare_location_impact_location_without_country(self):
        impact_location = self.create_geolocation(
            country=None,
            locality='Amsterdam',
            formatted_address='Dam 1, Amsterdam',
        )
        funding = FundingFactory.create(impact_location=impact_location)

        document = FundingDocument()
        locations = document.prepare_location(funding)

        self.assertEqual(len(locations), 1)
        self.assertEqual(locations[0]['id'], impact_location.id)
        self.assertEqual(locations[0]['name'], 'Dam 1, Amsterdam')
        self.assertEqual(locations[0]['locality'], 'Amsterdam')
        self.assertIsNone(locations[0]['country_code'])
        self.assertIsNone(locations[0]['country'])
        self.assertEqual(locations[0]['type'], 'location')

    def test_prepare_indexing_impact_location_without_country(self):
        impact_location = self.create_geolocation(
            country=None,
            locality='Amsterdam',
            formatted_address='Dam 1, Amsterdam',
        )
        funding = FundingFactory.create(impact_location=impact_location)

        prepared = FundingDocument().prepare(funding)

        self.assertEqual(
            prepared['location'],
            [{
                'id': impact_location.id,
                'name': 'Dam 1, Amsterdam',
                'locality': 'Amsterdam',
                'country_code': None,
                'country': None,
                'type': 'location',
            }],
        )
