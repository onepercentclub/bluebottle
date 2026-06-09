from __future__ import annotations

from unittest import mock

import requests

from bluebottle.geo.mapbox import V6_FORWARD_URL, V6_REVERSE_URL

_mapbox_get_patcher = None
_original_requests_get = requests.get

MAPBOX_V5_FEATURE = {
    'id': 'address.8367876655690618',
    'type': 'Feature',
    'place_type': ['address'],
    'relevance': 1,
    'properties': {
        'accuracy': 'rooftop',
        'mapbox_id': 'dXJuOm1ieGFkcjowYzM5NTBjMi0wMjNhLTQxNTUtOTRmOS1kZTFmZDcxOWQwMTY',
    },
    'text': 'Brouwersdam Buitenzijde',
    'place_name': 'Brouwersdam Buitenzijde 20, 3253 MM Ouddorp, Netherlands',
    'center': [3.851166, 51.762731],
    'geometry': {'type': 'Point', 'coordinates': [3.851166, 51.762731]},
    'address': '20',
    'context': [
        {'id': 'postcode.8367876655690618', 'text': '3253 MM'},
        {
            'id': 'place.12961960',
            'mapbox_id': 'dXJuOm1ieHBsYzp4Y2lv',
            'wikidata': 'Q21060',
            'text': 'Ouddorp',
        },
        {
            'id': 'region.25768',
            'mapbox_id': 'dXJuOm1ieHBsYzpaS2c',
            'wikidata': 'Q694',
            'short_code': 'NL-ZH',
            'text': 'South Holland',
        },
        {
            'id': 'country.8872',
            'mapbox_id': 'dXJuOm1ieHBsYzpJcWc',
            'wikidata': 'Q55',
            'short_code': 'nl',
            'text': 'Netherlands',
        },
    ],
}

MAPBOX_V6_CONTEXT = {
    'address': {
        'mapbox_id': 'dXJuOm1ieGFkcjp0ZXN0LWFkZHJlc3M',
        'name': 'Test Street 1',
        'translations': {'en': {'name': 'Test Street 1'}, 'nl': {'name': 'Teststraat 1'}},
    },
    'street': {
        'mapbox_id': 'dXJuOm1ieGFkcjp0ZXN0LXN0cmVldA',
        'name': 'Test Street',
        'translations': {'en': {'name': 'Test Street'}, 'nl': {'name': 'Teststraat'}},
    },
    'place': {
        'mapbox_id': 'dXJuOm1ieGFkcjp0ZXN0LXBsYWNl',
        'name': 'Amsterdam',
        'translations': {'en': {'name': 'Amsterdam'}, 'nl': {'name': 'Amsterdam'}},
    },
    'postcode': {
        'mapbox_id': 'dXJuOm1ieGFkcjp0ZXN0LXBvc3Rjb2Rl',
        'name': '1012 AB',
        'translations': {'en': {'name': '1012 AB'}, 'nl': {'name': '1012 AB'}},
    },
    'region': {
        'mapbox_id': 'dXJuOm1ieGFkcjp0ZXN0LXJlZ2lvbg',
        'name': 'North Holland',
        'short_code': 'NL-NH',
        'translations': {
            'en': {'name': 'North Holland'},
            'nl': {'name': 'Noord-Holland'},
        },
    },
    'country': {
        'mapbox_id': 'dXJuOm1ieGFkcjp0ZXN0LWNvdW50cnk',
        'name': 'Netherlands',
        'country_code': 'NL',
        'translations': {'en': {'name': 'Netherlands'}, 'nl': {'name': 'Nederland'}},
    },
}

MAPBOX_V6_FEATURE = {
    'id': 'dXJuOm1ieGFkcjp0ZXN0LWFkZHJlc3M',
    'type': 'Feature',
    'geometry': {'type': 'Point', 'coordinates': [4.9041, 52.3676]},
    'properties': {
        'feature_type': 'address',
        'mapbox_id': 'dXJuOm1ieGFkcjp0ZXN0LWFkZHJlc3M',
        'full_address': 'Test Street 1, 1012 AB Amsterdam, Netherlands',
        'name': 'Test Street 1',
        'context': MAPBOX_V6_CONTEXT,
    },
}


def _mock_response(payload, status_code=200):
    response = mock.MagicMock()
    response.status_code = status_code
    response.text = ''
    response.json.return_value = payload
    response.raise_for_status = mock.MagicMock()
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f'{status_code} error',
            response=response,
        )
    return response


def _is_mapbox_url(url):
    return 'api.mapbox.com' in str(url)


def mock_mapbox_requests_get(url, params=None, **kwargs):
    if not _is_mapbox_url(url):
        return _original_requests_get(url, params=params, **kwargs)

    url = str(url)
    if (
        V6_FORWARD_URL in url
        or V6_REVERSE_URL in url
        or '/search/geocode/v6/forward' in url
        or '/search/geocode/v6/reverse' in url
    ):
        return _mock_response({'features': [MAPBOX_V6_FEATURE]})

    if '/geocoding/v5/mapbox.places/' in url:
        return _mock_response({'features': [MAPBOX_V5_FEATURE]})

    return _mock_response({'features': []})


def install_mapbox_mock():
    global _mapbox_get_patcher, _original_requests_get
    if _mapbox_get_patcher is not None:
        return
    _original_requests_get = requests.get
    _mapbox_get_patcher = mock.patch('requests.get', side_effect=mock_mapbox_requests_get)
    _mapbox_get_patcher.start()


def uninstall_mapbox_mock():
    global _mapbox_get_patcher
    if _mapbox_get_patcher is None:
        return
    _mapbox_get_patcher.stop()
    _mapbox_get_patcher = None
