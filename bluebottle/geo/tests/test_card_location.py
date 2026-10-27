from bluebottle.geo import serializers as location_serializers
from bluebottle.test.utils import BluebottleTestCase


class CardLocationFormatTestCase(BluebottleTestCase):

    def _geofeature(self, feature_type, name, language='en', **extra):
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

    def _full_hierarchy(self, language='en'):
        return [
            self._geofeature('neighborhood', 'Scheveningen', language),
            self._geofeature('place', 'The Hague', language),
            self._geofeature('region', 'South Holland', language),
            self._geofeature('country', 'Netherlands', language),
        ]

    def test_city_country(self):
        geofeatures = [
            self._geofeature('place', 'Ouddorp'),
            self._geofeature('country', 'Netherlands'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            location_serializers.format_card_location(
                activity, 'city_country', 'en'
            ),
            'Ouddorp, NL',
        )

    def test_city_country_ignores_full_address_primary(self):
        geofeatures = [
            self._geofeature(
                'address',
                'Brouwersdam Buitenzijde 20',
                place_name=(
                    'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands'
                ),
                is_primary=True,
            ),
            self._geofeature('place', 'Ouddorp'),
            self._geofeature('country', 'Netherlands'),
        ]
        activity = type('Activity', (), {'geofeature': geofeatures, 'country': []})()

        self.assertEqual(
            location_serializers.format_card_location(
                activity, 'city_country', 'en', geofeatures=geofeatures
            ),
            'Ouddorp, NL',
        )

    def test_neighbourhood(self):
        activity = type('Activity', (), {
            'geofeature': self._full_hierarchy(),
            'country': [],
        })()

        self.assertEqual(
            location_serializers.format_card_location(
                activity, 'neighbourhood', 'en'
            ),
            'Scheveningen',
        )

    def test_neighbourhood_city(self):
        activity = type('Activity', (), {
            'geofeature': self._full_hierarchy(),
            'country': [],
        })()

        self.assertEqual(
            location_serializers.format_card_location(
                activity, 'neighbourhood_city', 'en'
            ),
            'Scheveningen, The Hague',
        )

    def test_city(self):
        activity = type('Activity', (), {
            'geofeature': self._full_hierarchy(),
            'country': [],
        })()

        self.assertEqual(
            location_serializers.format_card_location(activity, 'city', 'en'),
            'The Hague',
        )

    def test_city_region(self):
        activity = type('Activity', (), {
            'geofeature': self._full_hierarchy(),
            'country': [],
        })()

        self.assertEqual(
            location_serializers.format_card_location(
                activity, 'city_region', 'en'
            ),
            'The Hague, South Holland',
        )

    def test_language_filter(self):
        activity = type('Activity', (), {'country': []})()
        geofeatures = [
            self._geofeature('place', 'Berlijn', 'nl'),
            self._geofeature('country', 'Duitsland', 'nl', country_code='DE'),
        ]

        self.assertIsNone(
            location_serializers.format_card_location(
                activity, 'city_country', 'en', geofeatures=geofeatures
            )
        )
        self.assertEqual(
            location_serializers.format_card_location(
                activity, 'city_country', 'nl', geofeatures=geofeatures
            ),
            'Berlijn, DE',
        )

    def test_common_location_ignores_none_parts(self):
        activity = type('Activity', (), {'country': []})()
        parts = [
            {
                'neighborhood': None,
                'locality': None,
                'city': 'Amsterdam',
                'region': None,
                'country': 'Netherlands',
                'country_code': 'NL',
            },
            None,
        ]

        self.assertIsNone(
            location_serializers.format_common_card_location(
                activity, 'city_country', 'en', parts
            )
        )
