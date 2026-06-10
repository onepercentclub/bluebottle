from unittest import mock

from django.contrib.gis.geos import Point

from bluebottle.geo import mapbox as mapbox_utils
from bluebottle.geo.models import GeoFeature, Geolocation
from bluebottle.geo.tests.mapbox_fixtures import MAPBOX_V6_ADDRESS_FEATURE
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.utils import BluebottleTestCase


class MapboxUtilsTestCase(BluebottleTestCase):

    def test_is_v6_mapbox_id(self):
        self.assertTrue(mapbox_utils.is_v6_mapbox_id('dXJuOm1ieGFkcjox'))
        self.assertFalse(mapbox_utils.is_v6_mapbox_id('address.123'))
        self.assertFalse(mapbox_utils.is_v6_mapbox_id(''))

    def test_normalize_reverse_type(self):
        self.assertEqual(mapbox_utils._normalize_reverse_type('address'), 'address')
        self.assertEqual(mapbox_utils._normalize_reverse_type(['address']), 'address')
        self.assertIsNone(mapbox_utils._normalize_reverse_type(['address', 'place']))

    @mock.patch('bluebottle.geo.mapbox._request')
    def test_reverse_v6_omits_limit_for_multiple_types(self, mock_request):
        mock_request.return_value = {'features': []}
        mapbox_utils.reverse_v6(4.85, 52.39, types=['address', 'place'], limit=5)

        params = mock_request.call_args[0][1]
        self.assertNotIn('types', params)
        self.assertNotIn('limit', params)

    @mock.patch('bluebottle.geo.mapbox._request')
    def test_reverse_v6_allows_limit_with_single_type(self, mock_request):
        mock_request.return_value = {'features': []}
        mapbox_utils.reverse_v6(4.85, 52.39, types='address', limit=1)

        params = mock_request.call_args[0][1]
        self.assertEqual(params['types'], 'address')
        self.assertEqual(params['limit'], 1)

    def test_extract_housenumber_from_street_number(self):
        geolocation = Geolocation(street_number='30')
        self.assertEqual(mapbox_utils.extract_housenumber(geolocation), '30')

    def test_extract_housenumber_from_formatted_address(self):
        geolocation = Geolocation(formatted_address='Hansenstraat 30, Leiden')
        self.assertEqual(mapbox_utils.extract_housenumber(geolocation), '30')

    def test_parse_feature(self):
        parsed = mapbox_utils.parse_feature(MAPBOX_V6_ADDRESS_FEATURE)
        self.assertEqual(
            parsed['mapbox_id'],
            MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id'],
        )
        self.assertEqual(parsed['locality'], 'Ouddorp')
        self.assertEqual(parsed['street_number'], '20')
        self.assertEqual(parsed['country_code'], 'NL')

    @mock.patch('bluebottle.geo.mapbox.forward_v6')
    def test_resolve_geolocation_feature_for_address_v5_id(self, mock_forward):
        country = CountryFactory.create(alpha2_code='NL')
        geolocation = Geolocation(
            mapbox_id='address.8367876655690618',
            street='Hansenstraat',
            street_number='30',
            locality='Leiden',
            postal_code='2312',
            country=country,
        )
        mock_forward.return_value = {'features': [MAPBOX_V6_ADDRESS_FEATURE]}

        feature = mapbox_utils.resolve_geolocation_feature(geolocation)

        self.assertEqual(feature, MAPBOX_V6_ADDRESS_FEATURE)
        mock_forward.assert_called_once()
        self.assertEqual(mock_forward.call_args.kwargs['address_number'], '30')
        self.assertEqual(mock_forward.call_args.kwargs['street'], 'Hansenstraat')
        self.assertEqual(mock_forward.call_args.kwargs['types'], ['address'])

    def test_sync_geofeatures(self):
        country = CountryFactory.create(alpha2_code='NL')
        geolocation = Geolocation.objects.create(
            position=Point(3.851166, 51.762731),
            mapbox_id=MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id'],
            country=country,
        )

        mapbox_utils.sync_geofeatures(geolocation, MAPBOX_V6_ADDRESS_FEATURE)

        self.assertGreater(geolocation.geofeatures.count(), 0)
        address_feature = GeoFeature.objects.get(
            mapbox_id=MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id'],
        )
        self.assertEqual(address_feature.feature_type, 'address')
        self.assertEqual(
            address_feature.place_name,
            MAPBOX_V6_ADDRESS_FEATURE['properties']['full_address'],
        )
        self.assertEqual(
            address_feature.safe_translation_getter('name', any_language=True),
            MAPBOX_V6_ADDRESS_FEATURE['properties']['name'],
        )

    def test_sync_geofeatures_creates_translations_for_new_features(self):
        country = CountryFactory.create(alpha2_code='NL')
        geolocation = Geolocation.objects.create(
            position=Point(3.851166, 51.762731),
            country=country,
        )
        feature = {
            'type': 'Feature',
            'properties': {
                'mapbox_id': 'dXJuOm1ieGFkcjpuZXdjb3VudHJ5',
                'feature_type': 'country',
                'name': 'Netherlands',
                'full_address': 'Netherlands',
                'context': {
                    'country': {
                        'mapbox_id': 'dXJuOm1ieGFkcjpuZXdjb3VudHJ5',
                        'name': 'Netherlands',
                        'country_code': 'NL',
                    },
                },
            },
        }

        mapbox_utils.sync_geofeatures(geolocation, feature)

        geofeature = GeoFeature.objects.get(mapbox_id='dXJuOm1ieGFkcjpuZXdjb3VudHJ5')
        self.assertEqual(geofeature.safe_translation_getter('name', any_language=True), 'Netherlands')
        self.assertEqual(geofeature.safe_translation_getter('place_name', any_language=True), 'Netherlands')

    @mock.patch(
        'bluebottle.geo.models.Geolocation.reverse_geocode',
        return_value=MAPBOX_V6_ADDRESS_FEATURE,
    )
    def test_geolocation_save_reverse_geocodes_position(self, mock_reverse_geocode):
        country = CountryFactory.create(alpha2_code='NL')
        geolocation = Geolocation(
            position=Point(3.851166, 51.762731),
            country=country,
        )
        geolocation.save()

        self.assertEqual(
            geolocation.mapbox_id,
            MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id'],
        )
        self.assertEqual(geolocation.locality, 'Ouddorp')
        self.assertEqual(
            geolocation.formatted_address,
            MAPBOX_V6_ADDRESS_FEATURE['properties']['full_address'],
        )
        self.assertGreater(geolocation.geofeatures.count(), 0)
