from copy import deepcopy
from unittest import mock

from django.contrib.gis.geos import Point

from bluebottle.geo import mapbox as mapbox_utils
from bluebottle.geo.models import GeoFeature, Geolocation
from bluebottle.geo.tests.mapbox_fixtures import MAPBOX_V6_ADDRESS_FEATURE
from bluebottle.test.factory_models.geo import CountryFactory
from bluebottle.test.factory_models.utils import LanguageFactory
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

    @mock.patch('bluebottle.geo.mapbox.forward_v6')
    def test_lookup_by_mapbox_id_requests_platform_languages(self, mock_forward):
        LanguageFactory.create(code='en', language_name='English', native_name='English', default=True)
        LanguageFactory.create(code='nl', language_name='Dutch', native_name='Nederlands')
        mock_forward.return_value = {'features': []}

        mapbox_utils.lookup_by_mapbox_id('dXJuOm1ieGFkcjox', language='en')

        self.assertEqual(mock_forward.call_args.kwargs['language'], 'en,nl')

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

        translations = mapbox_utils.get_translated_geofeature_list(geofeature, country=country)
        languages = {entry['language'] for entry in translations}

        self.assertIn('en', languages)
        self.assertIn('nl', languages)
        self.assertEqual(
            next(entry for entry in translations if entry['language'] == 'nl')['place_name'],
            'Ouddorp, Nederland',
        )
        self.assertEqual(translations[0]['feature_type'], 'place')

    def _card_location_geofeature(self, feature_type, name, language='en', **extra):
        defaults = {
            'language': language,
            'name': name,
            'place_name': name,
            'feature_type': feature_type,
            'is_primary': False,
            'country': 'Netherlands',
            'country_code': 'NL',
        }
        defaults.update(extra)
        return type('GeoFeature', (), defaults)()

    def _full_hierarchy_geofeatures(self, language='en'):
        return [
            self._card_location_geofeature('neighborhood', 'Scheveningen', language),
            self._card_location_geofeature('place', 'The Hague', language),
            self._card_location_geofeature('region', 'South Holland', language),
            self._card_location_geofeature('country', 'Netherlands', language),
        ]

    def test_format_card_location_city_country(self):
        geofeatures = [
            self._card_location_geofeature('place', 'Ouddorp', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city_country', 'en'),
            'Ouddorp, NL',
        )

    def test_format_card_location_city_country_legacy_multiselect(self):
        geofeatures = [
            self._card_location_geofeature('place', 'Ouddorp', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, ['place', 'country_code'], 'en'),
            'Ouddorp, NL',
        )

    def test_format_card_location_country_only(self):
        geofeatures = [
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city_country', 'en'),
            'Netherlands',
        )

    def test_format_card_location_uses_country_fallback(self):
        activity = type('Activity', (), {
            'geofeature': [
                self._card_location_geofeature(
                    'place',
                    'Ouddorp',
                    'nl',
                    country='Nederland',
                ),
            ],
            'country': [
                type('Country', (), {
                    'language': 'nl',
                    'name': 'Nederland',
                })(),
            ],
        })()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city_country', 'nl'),
            'Ouddorp, NL',
        )

    def test_format_card_location_neighbourhood_mode(self):
        activity = type('Activity', (), {
            'geofeature': self._full_hierarchy_geofeatures(),
            'country': [],
        })()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'neighbourhood', 'en'),
            'Scheveningen',
        )

    def test_format_card_location_neighbourhood_fallback_to_city(self):
        geofeatures = [
            self._card_location_geofeature('place', 'The Hague', 'en'),
            self._card_location_geofeature('region', 'South Holland', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'neighbourhood', 'en'),
            'The Hague',
        )

    def test_format_card_location_neighbourhood_city_mode(self):
        activity = type('Activity', (), {
            'geofeature': self._full_hierarchy_geofeatures(),
            'country': [],
        })()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'neighbourhood_city', 'en'),
            'Scheveningen, The Hague',
        )

    def test_format_card_location_neighbourhood_city_city_only(self):
        geofeatures = [
            self._card_location_geofeature('place', 'The Hague', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'neighbourhood_city', 'en'),
            'The Hague',
        )

    def test_format_card_location_neighbourhood_city_region_fallback(self):
        geofeatures = [
            self._card_location_geofeature('region', 'South Holland', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'neighbourhood_city', 'en'),
            'South Holland',
        )

    def test_format_card_location_city_mode(self):
        activity = type('Activity', (), {
            'geofeature': self._full_hierarchy_geofeatures(),
            'country': [],
        })()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city', 'en'),
            'The Hague',
        )

    def test_format_card_location_city_fallback_to_region(self):
        geofeatures = [
            self._card_location_geofeature('region', 'South Holland', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city', 'en'),
            'South Holland',
        )

    def test_format_card_location_city_region_mode(self):
        activity = type('Activity', (), {
            'geofeature': self._full_hierarchy_geofeatures(),
            'country': [],
        })()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city_region', 'en'),
            'The Hague, South Holland',
        )

    def test_format_card_location_city_region_region_only(self):
        geofeatures = [
            self._card_location_geofeature('region', 'South Holland', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city_region', 'en'),
            'South Holland',
        )

    def test_format_card_location_city_region_country_fallback(self):
        geofeatures = [
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city_region', 'en'),
            'Netherlands',
        )

    def test_format_card_location_city_country_region_and_country(self):
        geofeatures = [
            self._card_location_geofeature('region', 'South Holland', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city_country', 'en'),
            'South Holland, NL',
        )

    def test_format_card_location_city_uses_locality_fallback(self):
        geofeatures = [
            self._card_location_geofeature('locality', 'Ouddorp', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            mapbox_utils.format_card_location(activity, 'city', 'en'),
            'Ouddorp',
        )

    def test_format_card_location_from_values(self):
        self.assertEqual(
            mapbox_utils.format_card_location_from_values(
                'city_country',
                city='Ouddorp',
                country='Netherlands',
                country_code='NL',
            ),
            'Ouddorp, NL',
        )
        self.assertEqual(
            mapbox_utils.format_card_location_from_values(
                'neighbourhood_city',
                neighborhood='Scheveningen',
                city='The Hague',
            ),
            'Scheveningen, The Hague',
        )

    def test_format_common_card_location_same_country(self):
        activity = type('Activity', (), {'country': []})()
        amsterdam = [
            self._card_location_geofeature('place', 'Amsterdam', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        rotterdam = [
            self._card_location_geofeature('place', 'Rotterdam', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        location_parts = [
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, amsterdam, 'en'
            ),
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, rotterdam, 'en'
            ),
        ]

        self.assertEqual(
            mapbox_utils.format_common_card_location(
                activity, 'city_country', 'en', location_parts
            ),
            'NL',
        )

    def test_format_common_card_location_same_region(self):
        activity = type('Activity', (), {'country': []})()
        the_hague = self._full_hierarchy_geofeatures()
        delft = [
            self._card_location_geofeature('place', 'Delft', 'en'),
            self._card_location_geofeature('region', 'South Holland', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        location_parts = [
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, the_hague, 'en'
            ),
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, delft, 'en'
            ),
        ]

        self.assertEqual(
            mapbox_utils.format_common_card_location(
                activity, 'city_country', 'en', location_parts
            ),
            'South Holland, NL',
        )

    def test_format_multi_neighbourhood_city_different_neighborhoods_same_city(self):
        activity = type('Activity', (), {'country': []})()
        scheveningen = [
            self._card_location_geofeature('neighborhood', 'Scheveningen', 'en'),
            self._card_location_geofeature('place', 'The Hague', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        centrum = [
            self._card_location_geofeature('neighborhood', 'Centrum', 'en'),
            self._card_location_geofeature('place', 'The Hague', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        location_parts = [
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, scheveningen, 'en'
            ),
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, centrum, 'en'
            ),
        ]

        self.assertEqual(
            mapbox_utils.format_common_card_location(
                activity, 'neighbourhood_city', 'en', location_parts
            ),
            'The Hague',
        )

    def test_format_multi_neighbourhood_city_same_neighborhood_and_city(self):
        activity = type('Activity', (), {'country': []})()
        location_a = [
            self._card_location_geofeature('neighborhood', 'Scheveningen', 'en'),
            self._card_location_geofeature('place', 'The Hague', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        location_b = [
            self._card_location_geofeature('neighborhood', 'Scheveningen', 'en'),
            self._card_location_geofeature('place', 'The Hague', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        location_parts = [
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, location_a, 'en'
            ),
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, location_b, 'en'
            ),
        ]

        self.assertEqual(
            mapbox_utils.format_common_card_location(
                activity, 'neighbourhood_city', 'en', location_parts
            ),
            'Scheveningen, The Hague',
        )

    def test_format_multi_city_country_different_cities_same_region(self):
        activity = type('Activity', (), {'country': []})()
        amsterdam = [
            self._card_location_geofeature('place', 'Amsterdam', 'en'),
            self._card_location_geofeature('region', 'North Holland', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        haarlem = [
            self._card_location_geofeature('place', 'Haarlem', 'en'),
            self._card_location_geofeature('region', 'North Holland', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        location_parts = [
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, amsterdam, 'en'
            ),
            mapbox_utils.card_location_parts_from_geofeatures(
                activity, haarlem, 'en'
            ),
        ]

        self.assertEqual(
            mapbox_utils.format_common_card_location(
                activity, 'city_country', 'en', location_parts
            ),
            'North Holland, NL',
        )

    def test_format_common_card_location_no_common_feature(self):
        activity = type('Activity', (), {'country': []})()
        nl = [
            self._card_location_geofeature('place', 'Amsterdam', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        de = [
            self._card_location_geofeature('place', 'Berlin', 'en'),
            self._card_location_geofeature('country', 'Germany', 'en', country_code='DE'),
        ]
        location_parts = [
            mapbox_utils.card_location_parts_from_geofeatures(activity, nl, 'en'),
            mapbox_utils.card_location_parts_from_geofeatures(activity, de, 'en'),
        ]

        self.assertIsNone(
            mapbox_utils.format_common_card_location(
                activity, 'city_country', 'en', location_parts
            )
        )

    def test_common_formatted_address_same_street_different_numbers(self):
        location_a = [
            self._card_location_geofeature(
                'address', 'Louis Armstronglaan 780, 3543 EB Utrecht, Netherlands', 'en'
            ),
            self._card_location_geofeature('street', 'Louis Armstronglaan', 'en'),
            self._card_location_geofeature('postcode', '3543 EB', 'en'),
            self._card_location_geofeature('place', 'Utrecht', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        location_b = [
            self._card_location_geofeature(
                'address', 'Louis Armstronglaan 800, 3543 EB Utrecht, Netherlands', 'en'
            ),
            self._card_location_geofeature('street', 'Louis Armstronglaan', 'en'),
            self._card_location_geofeature('postcode', '3543 EB', 'en'),
            self._card_location_geofeature('place', 'Utrecht', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]

        self.assertEqual(
            mapbox_utils.common_formatted_address_from_geofeatures(
                [location_a, location_b], 'en'
            ),
            'Louis Armstronglaan, 3543 EB Utrecht, Netherlands',
        )

    def test_common_formatted_address_same_country_different_cities(self):
        amsterdam = [
            self._card_location_geofeature('place', 'Amsterdam', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]
        rotterdam = [
            self._card_location_geofeature('place', 'Rotterdam', 'en'),
            self._card_location_geofeature('country', 'Netherlands', 'en'),
        ]

        self.assertEqual(
            mapbox_utils.common_formatted_address_from_geofeatures(
                [amsterdam, rotterdam], 'en'
            ),
            'Netherlands',
        )

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
        geolocation.refresh_from_db()
        self.assertEqual(geolocation.geofeature.feature_type, 'address')
