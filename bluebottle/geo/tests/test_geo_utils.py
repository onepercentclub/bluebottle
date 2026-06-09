from django.test import TestCase

from bluebottle.geo.geofeatures import sync_geolocation
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory
from bluebottle.test.mapbox_mocks import MAPBOX_V6_FEATURE


class SyncGeolocationTest(TestCase):
    def setUp(self):
        self.netherlands = CountryFactory.create(alpha2_code='NL')

    def test_sync_geolocation_links_features_and_country(self):
        geolocation = GeolocationFactory.create(
            mapbox_id=MAPBOX_V6_FEATURE['id'],
            country=None,
            geofeatures=False,
        )
        geolocation.refresh_from_db()
        self.assertEqual(geolocation.country, self.netherlands)
        self.assertTrue(geolocation.features.filter(place_type='country').exists())
        self.assertTrue(geolocation.features.filter(place_type='address').exists())

    def test_sync_geolocation_without_mapbox_id(self):
        geolocation = GeolocationFactory.build(mapbox_id=None, geofeatures=False)
        geolocation.save()
        self.assertEqual(sync_geolocation(geolocation), 0)
