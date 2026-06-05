from django.test import TestCase

from unittest import mock

from bluebottle.geo.geofeatures import _resolve_place_name, format_place_name


LEIDEN_CONTEXT = {
    'address': {
        'mapbox_id': 'address.123',
        'name': 'Hansenstraat 30',
        'translations': {'en': {'name': 'Hansenstraat 30'}},
    },
    'street': {
        'mapbox_id': 'street.123',
        'name': 'Hansenstraat',
        'translations': {'en': {'name': 'Hansenstraat'}},
    },
    'place': {
        'mapbox_id': 'place.123',
        'name': 'Leiden',
        'translations': {'en': {'name': 'Leiden'}},
    },
    'postcode': {
        'mapbox_id': 'postcode.123',
        'name': '2316 BJ',
        'translations': {'en': {'name': '2316 BJ'}},
    },
    'region': {
        'mapbox_id': 'region.123',
        'name': 'South Holland',
        'translations': {
            'en': {'name': 'South Holland'},
            'nl': {'name': 'Zuid-Holland'},
        },
    },
    'country': {
        'mapbox_id': 'country.123',
        'name': 'Netherlands',
        'country_code': 'NL',
        'translations': {
            'en': {'name': 'Netherlands'},
            'nl': {'name': 'Nederland'},
        },
    },
}


def _ctx_feature(place_type):
    ctx = LEIDEN_CONTEXT[place_type]
    return {
        'text': ctx.get('name'),
        'translations': ctx.get('translations') or {},
        'context': LEIDEN_CONTEXT,
        'properties': {
            'context': LEIDEN_CONTEXT,
            'full_address': 'Hansenstraat 30, 2316 BJ Leiden, Netherlands',
            'feature_type': place_type,
        },
    }


class FormatPlaceNameTest(TestCase):
    def test_address_place_name_includes_city_and_country_without_addressformatting(self):
        props = _ctx_feature('address')['properties']
        feature = _ctx_feature('address')

        formatted = format_place_name('address', feature, props, 'en', formatter=None)

        self.assertNotEqual(formatted, 'Hansenstraat 30')
        self.assertIn('Leiden', formatted)
        self.assertIn('Netherlands', formatted)

    def test_street_place_name_includes_city_and_country_without_addressformatting(self):
        props = _ctx_feature('street')['properties']
        feature = _ctx_feature('street')

        formatted = format_place_name('street', feature, props, 'en', formatter=None)

        self.assertEqual(formatted, 'Hansenstraat, Leiden, Netherlands')

    def test_place_name_uses_mapbox_full_address_when_formatter_unavailable(self):
        props = _ctx_feature('address')['properties']
        feature = _ctx_feature('address')

        place_name = _resolve_place_name(
            'address', feature, props, 'en', formatter=None, text_value='Hansenstraat 30',
        )

        self.assertIn('Leiden', place_name)
        self.assertIn('Netherlands', place_name)
        self.assertNotEqual(place_name, 'Hansenstraat 30')

    def test_postcode_place_name_includes_city_and_country(self):
        props = _ctx_feature('postcode')['properties']
        feature = _ctx_feature('postcode')

        formatted = format_place_name('postcode', feature, props, 'en', formatter=None)

        self.assertEqual(formatted, '2316 BJ, Leiden, Netherlands')

    def test_address_place_name_uses_fallback_when_formatter_returns_bare_street(self):
        props = _ctx_feature('address')['properties']
        feature = _ctx_feature('address')
        formatter = mock.Mock()
        formatter.one_line.return_value = 'Hansenstraat 30'

        formatted = format_place_name('address', feature, props, 'en', formatter=formatter)

        self.assertIn('Leiden', formatted)
        self.assertIn('Netherlands', formatted)
        self.assertNotEqual(formatted, 'Hansenstraat 30')
