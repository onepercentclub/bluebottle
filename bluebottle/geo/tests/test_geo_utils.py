from django.test import TestCase

from bluebottle.geo.models import Country
from bluebottle.geo.utils import (
    resolve_country_from_code,
    resolve_country_from_mapbox_context,
    resolve_country_from_mapbox_feature,
    sync_geolocation_country,
)
from bluebottle.test.factory_models.geo import CountryFactory, GeolocationFactory


class CountryResolutionTest(TestCase):
    def setUp(self):
        self.netherlands = CountryFactory.create(alpha2_code='NL')

    def test_resolve_country_from_code(self):
        self.assertEqual(resolve_country_from_code('nl'), self.netherlands)
        self.assertEqual(resolve_country_from_code('NL-ZH'), self.netherlands)

    def test_resolve_country_from_v6_context(self):
        context = {
            'country': {
                'name': 'Netherlands',
                'country_code': 'NL',
            },
        }
        self.assertEqual(resolve_country_from_mapbox_context(context), self.netherlands)

    def test_resolve_country_from_v5_context(self):
        context = [
            {'id': 'region.25768', 'short_code': 'NL-ZH', 'text': 'South Holland'},
            {'id': 'country.8872', 'short_code': 'nl', 'text': 'Netherlands'},
        ]
        self.assertEqual(resolve_country_from_mapbox_context(context), self.netherlands)

    def test_resolve_country_when_feature_is_country(self):
        feature = {
            'place_type': ['country'],
            'properties': {'short_code': 'nl'},
        }
        self.assertEqual(resolve_country_from_mapbox_feature(feature), self.netherlands)

    def test_sync_geolocation_country_from_context(self):
        geolocation = GeolocationFactory.create(country=None)
        context = {'country': {'country_code': 'NL'}}
        sync_geolocation_country(geolocation, context=context)
        geolocation.refresh_from_db()
        self.assertEqual(geolocation.country, self.netherlands)
