from copy import deepcopy
from importlib.machinery import SourceFileLoader
from pathlib import Path
from unittest import mock

from django.contrib.gis.geos import Point

from bluebottle.activities.documents import get_translated_geofeature_list
from bluebottle.geo import mapbox as mapbox_utils
from bluebottle.geo.models import GeoFeature, Geolocation
from bluebottle.geo.tests.mapbox_fixtures import MAPBOX_V6_ADDRESS_FEATURE
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.utils import LanguageFactory
from bluebottle.test.utils import BluebottleTestCase

migrate_mapbox = SourceFileLoader(
    'migrate_mapbox',
    str(Path(__file__).resolve().parents[3] / 'scripts' / 'migrate_mapbox.py'),
).load_module()


class MapboxUtilsTestCase(BluebottleTestCase):

    def test_is_v6_mapbox_id(self):
        self.assertTrue(mapbox_utils.is_v6_mapbox_id('dXJuOm1ieGFkcjox'))
        self.assertFalse(mapbox_utils.is_v6_mapbox_id('address.123'))
        self.assertFalse(mapbox_utils.is_v6_mapbox_id(''))

    def test_extract_housenumber_from_street_number(self):
        geolocation = Geolocation(street_number='30')
        self.assertEqual(migrate_mapbox.extract_housenumber(geolocation), '30')

    def test_extract_housenumber_from_formatted_address(self):
        geolocation = Geolocation(formatted_address='Hansenstraat 30, Leiden')
        self.assertEqual(migrate_mapbox.extract_housenumber(geolocation), '30')

    def test_geofeature_place_name_hierarchy(self):
        context = MAPBOX_V6_ADDRESS_FEATURE['properties']['context']

        self.assertEqual(
            mapbox_utils.geofeature_place_name(
                'address',
                'Brouwersdam Buitenzijde 20',
                context,
                full_address=MAPBOX_V6_ADDRESS_FEATURE['properties']['full_address'],
            ),
            'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands',
        )
        self.assertEqual(
            mapbox_utils.geofeature_place_name('street', 'Brouwersdam Buitenzijde', context),
            'Brouwersdam Buitenzijde, Ouddorp, Netherlands',
        )
        self.assertEqual(
            mapbox_utils.geofeature_place_name('postcode', '3253 MM', context),
            '3253 MM, Ouddorp, Netherlands',
        )
        self.assertEqual(
            mapbox_utils.geofeature_place_name('place', 'Ouddorp', context),
            'Ouddorp, Netherlands',
        )
        self.assertEqual(
            mapbox_utils.geofeature_place_name('region', 'South Holland', context),
            'South Holland, Netherlands',
        )
        self.assertEqual(
            mapbox_utils.geofeature_place_name('country', 'Netherlands', context),
            'Netherlands',
        )

    def test_parse_feature(self):
        parsed = migrate_mapbox.parse_feature(MAPBOX_V6_ADDRESS_FEATURE)
        self.assertEqual(
            parsed['mapbox_id'],
            MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id'],
        )
        self.assertEqual(parsed['locality'], 'Ouddorp')
        self.assertEqual(parsed['street_number'], '20')
        self.assertEqual(parsed['country_code'], 'NL')

    @mock.patch('migrate_mapbox.forward_v6')
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

        feature = migrate_mapbox.resolve_geolocation_feature(geolocation)

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
        self.assertEqual(geolocation.geofeatures.count(), 0)
        self.assertIsNone(geolocation.geofeature_id)

        mapbox_utils.sync_geofeatures(geolocation, MAPBOX_V6_ADDRESS_FEATURE)

        geolocation.refresh_from_db()
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
        self.assertEqual(
            GeoFeature.objects.get(
                mapbox_id=MAPBOX_V6_ADDRESS_FEATURE['properties']['context']['postcode']['mapbox_id'],
            ).place_name,
            '3253 MM, Ouddorp, Netherlands',
        )
        self.assertEqual(
            GeoFeature.objects.get(
                mapbox_id=MAPBOX_V6_ADDRESS_FEATURE['properties']['context']['place']['mapbox_id'],
            ).place_name,
            'Ouddorp, Netherlands',
        )
        self.assertEqual(
            GeoFeature.objects.get(
                mapbox_id=MAPBOX_V6_ADDRESS_FEATURE['properties']['context']['region']['mapbox_id'],
            ).place_name,
            'South Holland, Netherlands',
        )
        self.assertEqual(
            GeoFeature.objects.get(
                mapbox_id=MAPBOX_V6_ADDRESS_FEATURE['properties']['context']['country']['mapbox_id'],
            ).place_name,
            'Netherlands',
        )
        self.assertEqual(geolocation.geofeature.feature_type, 'address')
        self.assertEqual(
            str(geolocation),
            MAPBOX_V6_ADDRESS_FEATURE['properties']['full_address'],
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

    def test_sync_geofeatures_applies_mapbox_translation_objects(self):
        LanguageFactory.create(code='en', language_name='English', native_name='English', default=True)
        LanguageFactory.create(code='nl', language_name='Dutch', native_name='Nederlands')
        country = CountryFactory.create(alpha2_code='NL')
        geolocation = Geolocation.objects.create(
            position=Point(3.851166, 51.762731),
            mapbox_id=MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id'],
            country=country,
        )

        feature = deepcopy(MAPBOX_V6_ADDRESS_FEATURE)
        context = feature['properties']['context']
        context['place']['translations'] = {
            'en': {'language': 'en', 'name': 'Ouddorp'},
            'nl': {'language': 'nl', 'name': 'Ouddorp'},
        }
        context['country']['translations'] = {
            'en': {'language': 'en', 'name': 'Netherlands'},
            'nl': {'language': 'nl', 'name': 'Nederland'},
        }

        mapbox_utils.sync_geofeatures(geolocation, feature, language='en')

        place_feature = GeoFeature.objects.get(
            mapbox_id=context['place']['mapbox_id'],
        )
        place_feature.set_current_language('nl')
        self.assertEqual(place_feature.name, 'Ouddorp')
        self.assertEqual(place_feature.place_name, 'Ouddorp, Nederland')

        country_feature = GeoFeature.objects.get(
            mapbox_id=context['country']['mapbox_id'],
        )
        country_feature.set_current_language('nl')
        self.assertEqual(country_feature.name, 'Nederland')

    @mock.patch('bluebottle.geo.mapbox.geocode_request')
    def test_lookup_by_mapbox_id_requests_platform_languages(self, mock_request):
        LanguageFactory.create(code='en', language_name='English', native_name='English', default=True)
        LanguageFactory.create(code='nl', language_name='Dutch', native_name='Nederlands')
        mock_request.return_value = {'features': []}

        mapbox_utils.lookup_by_mapbox_id('dXJuOm1ieGFkcjox', language='en')

        params = mock_request.call_args[0][1]
        self.assertCountEqual(params['language'].split(','), ['en', 'nl'])
        self.assertEqual(params['q'], 'dXJuOm1ieGFkcjox')

    def test_get_translated_geofeature_list(self):
        LanguageFactory.create(code='en', language_name='English', native_name='English', default=True)
        LanguageFactory.create(code='nl', language_name='Dutch', native_name='Nederlands')
        country = CountryFactory.create(alpha2_code='NL')
        geofeature = GeoFeature.objects.create(
            mapbox_id='dXJuOm1ieGFkcjox',
            feature_type='place',
        )
        geofeature.set_current_language('en')
        geofeature.name = 'Ouddorp'
        geofeature.place_name = 'Ouddorp, Netherlands'
        geofeature.save()

        geofeature.set_current_language('nl')
        geofeature.name = 'Ouddorp'
        geofeature.place_name = 'Ouddorp, Nederland'
        geofeature.save()

        translations = get_translated_geofeature_list(geofeature, country=country)
        languages = {entry['language'] for entry in translations}

        self.assertIn('en', languages)
        self.assertIn('nl', languages)
        self.assertEqual(
            next(entry for entry in translations if entry['language'] == 'nl')['place_name'],
            'Ouddorp, Nederland',
        )
        self.assertEqual(translations[0]['feature_type'], 'place')

    def test_get_translated_geofeature_list_skips_missing_translations(self):
        LanguageFactory.create(
            code='en', language_name='English', native_name='English', default=True
        )
        LanguageFactory.create(code='nl', language_name='Dutch', native_name='Nederlands')
        geofeature = GeoFeature.objects.create(
            mapbox_id='dXJuOm1ieGFkcjpuZWdjb2VudHJ5',
            feature_type='place',
        )
        geofeature.set_current_language('nl')
        geofeature.name = 'Berlijn'
        geofeature.place_name = 'Berlijn, Duitsland'
        geofeature.save()

        translations = get_translated_geofeature_list(geofeature)
        languages = {entry['language'] for entry in translations}

        self.assertEqual(languages, {'nl'})
        self.assertEqual(translations[0]['name'], 'Berlijn')

    @mock.patch(
        'bluebottle.geo.mapbox.lookup_by_mapbox_id',
        return_value={'features': [MAPBOX_V6_ADDRESS_FEATURE]},
    )
    def test_geolocation_save_syncs_geofeatures(self, mock_lookup):
        country = CountryFactory.create(alpha2_code='NL')
        geolocation = Geolocation(
            position=Point(3.851166, 51.762731),
            mapbox_id=MAPBOX_V6_ADDRESS_FEATURE['properties']['mapbox_id'],
            country=country,
        )
        geolocation.save()

        mock_lookup.assert_called_once()
        self.assertGreater(geolocation.geofeatures.count(), 0)
        geolocation.refresh_from_db()
        self.assertEqual(geolocation.geofeature.feature_type, 'address')
