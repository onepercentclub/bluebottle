import logging
import re

import requests

logger = logging.getLogger(__name__)
from django.conf import settings
from django.utils.translation import get_language

MAPBOX_GEOCODE_V6_BASE = 'https://api.mapbox.com/search/geocode/v6'

CONTEXT_TYPES = (
    'country', 'region', 'district', 'place',
    'locality', 'neighborhood', 'postcode', 'street', 'address',
)

FORMATTED_ADDRESS_HIERARCHY = (
    'address',
    'street',
    'postcode',
    'neighborhood',
    'locality',
    'place',
    'region',
    'country',
)

GEOFEATURE_TYPE_RANK = {
    feature_type: rank
    for rank, feature_type in enumerate(reversed(CONTEXT_TYPES))
}

HOUSE_NUMBER_LEADING_PATTERN = re.compile(r'^(\d+[a-zA-Z\-/]*)')
HOUSE_NUMBER_BEFORE_COMMA_PATTERN = re.compile(r'\b(\d+[a-zA-Z\-/]*)\s*,')


def is_v6_mapbox_id(value):
    return bool(value and value.startswith('dXJu'))


def needs_mapbox_id(value):
    return not value or value in ('', 'unknown') or not is_v6_mapbox_id(value)


def _housenumber_from_text(value):
    text = (value or '').strip()
    if not text:
        return None

    match = HOUSE_NUMBER_LEADING_PATTERN.search(text)
    if match:
        return match.group(1)

    match = HOUSE_NUMBER_BEFORE_COMMA_PATTERN.search(text)
    if match:
        return match.group(1)

    return None


def extract_housenumber(geolocation):
    if geolocation.street_number:
        return geolocation.street_number

    housenumber = _housenumber_from_text(geolocation.formatted_address)
    if housenumber:
        return housenumber

    return _housenumber_from_text(geolocation.street)


def _request(path, params):
    params = dict(params)
    params['access_token'] = settings.MAPBOX_API_KEY
    params['permanent'] = 'true'
    response = requests.get(
        '{}{}'.format(MAPBOX_GEOCODE_V6_BASE, path),
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def _first_feature(response):
    features = response.get('features', [])
    if features:
        return features[0]
    return None


def _prefer_address_feature(response):
    features = response.get('features', [])
    for feature in features:
        properties = feature.get('properties', {})
        if properties.get('feature_type') == 'address':
            return feature
    return features[0] if features else None


def forward_v6(
    query=None,
    address_number=None,
    street=None,
    postcode=None,
    place=None,
    region=None,
    country=None,
    types=None,
    language=None,
    limit=1,
):
    params = {'limit': limit}
    if language:
        params['language'] = language
    if types:
        params['types'] = ','.join(types) if isinstance(types, (list, tuple)) else types
    if query:
        params['q'] = query
    if address_number:
        params['address_number'] = address_number
    if street:
        params['street'] = street
    if postcode:
        params['postcode'] = postcode
    if place:
        params['place'] = place
    if region:
        params['region'] = region
    if country:
        params['country'] = country

    return _request('/forward', params)


def _normalize_reverse_type(types):
    if not types:
        return None
    if isinstance(types, (list, tuple)):
        if len(types) == 1:
            return types[0]
        return None
    return types


def reverse_v6(longitude, latitude, types=None, language=None, limit=None):
    params = {
        'longitude': longitude,
        'latitude': latitude,
    }
    if language:
        params['language'] = language

    type_value = _normalize_reverse_type(types)
    if type_value:
        params['types'] = type_value
        if limit is not None:
            params['limit'] = limit

    return _request('/reverse', params)


def reverse_geocode_feature(longitude, latitude, language=None):
    languages = platform_language_param(language)
    try:
        response = reverse_v6(
            longitude,
            latitude,
            types='address',
            language=languages,
            limit=1,
        )
        feature = _prefer_address_feature(response)
        if feature:
            return feature
    except requests.RequestException as error:
        logger.warning('Mapbox reverse geocode (address) failed: %s', error)

    try:
        response = reverse_v6(longitude, latitude, language=languages)
        return _prefer_address_feature(response)
    except requests.RequestException as error:
        logger.warning('Mapbox reverse geocode failed: %s', error)
        return None


def lookup_by_mapbox_id(mapbox_id, language=None):
    return forward_v6(
        query=mapbox_id,
        language=platform_language_param(language),
    )


def resolve_geolocation_feature(geolocation, language=None):
    language = language or get_language() or 'en'

    if geolocation.mapbox_id and not needs_mapbox_id(geolocation.mapbox_id):
        response = lookup_by_mapbox_id(geolocation.mapbox_id, language=language)
        return _first_feature(response)

    if geolocation.mapbox_id and geolocation.mapbox_id.startswith('address.'):
        address_number = extract_housenumber(geolocation)
        country_code = None
        if geolocation.country_id and geolocation.country:
            country_code = geolocation.country.alpha2_code

        params = {
            'street': geolocation.street,
            'postcode': geolocation.postal_code,
            'place': geolocation.locality,
            'region': geolocation.province,
            'country': country_code,
            'types': ['address'],
            'language': platform_language_param(language),
        }
        if address_number:
            params['address_number'] = address_number
            response = forward_v6(**params)
            feature = _prefer_address_feature(response)
            if feature:
                return feature

        if geolocation.formatted_address:
            response = forward_v6(
                query=geolocation.formatted_address,
                types=['address'],
                language=platform_language_param(language),
            )
            feature = _prefer_address_feature(response)
            if feature:
                return feature

    if geolocation.mapbox_id:
        response = lookup_by_mapbox_id(geolocation.mapbox_id, language=language)
        feature = _first_feature(response)
        if feature:
            return feature

    if geolocation.position:
        return reverse_geocode_feature(
            geolocation.position.x,
            geolocation.position.y,
            language=language,
        )

    if geolocation.formatted_address:
        response = forward_v6(
            query=geolocation.formatted_address,
            types=['address'],
            language=platform_language_param(language),
        )
        return _prefer_address_feature(response)

    return None


def _localized_context_name(context, feature_type, language=None):
    context_data = context.get(feature_type) or {}
    if not context_data:
        return ''

    if language:
        translations = context_data.get('translations') or {}
        localized = translations.get(language) or {}
        localized_name = localized.get('name')
        if localized_name:
            return localized_name

    return context_data.get('name', '')


def _city_name(context, language=None, exclude=()):
    for feature_type in ('place', 'locality'):
        if feature_type in exclude:
            continue
        name = _localized_context_name(context, feature_type, language)
        if name:
            return name
    return ''


def _country_name(context, language=None):
    return _localized_context_name(context, 'country', language)


def geofeature_place_name(feature_type, name, context=None, full_address=None, language=None):
    context = context if isinstance(context, dict) else {}
    name = (name or '').strip()

    if feature_type == 'address' and full_address:
        return full_address.strip()

    if not name:
        return (full_address or '').strip()

    country = _country_name(context, language)

    if feature_type == 'country':
        return name

    if feature_type == 'region':
        return ', '.join(part for part in (name, country) if part)

    if feature_type in ('place', 'locality'):
        return ', '.join(part for part in (name, country) if part)

    city = _city_name(
        context,
        language=language,
        exclude=(feature_type,) if feature_type in ('place', 'locality') else (),
    )
    return ', '.join(part for part in (name, city, country) if part)


def feature_place_name(properties, feature_type=None):
    properties = properties or {}
    context = properties.get('context', {})
    if not isinstance(context, dict):
        context = {}

    return geofeature_place_name(
        feature_type or properties.get('feature_type', ''),
        properties.get('name_preferred') or properties.get('name', ''),
        context,
        full_address=properties.get('full_address'),
    )


def translation_place_name(feature_type, name, context, translation=None, language=None):
    translation = translation or {}
    full_address = None
    if feature_type == 'address':
        full_address = translation.get('place_name') or translation.get('full_address')

    translated_name = translation.get('name') or name
    return geofeature_place_name(
        feature_type,
        translated_name,
        context,
        full_address=full_address,
        language=language,
    )


def platform_language_param(primary_language=None):
    from bluebottle.utils.models import Language

    if primary_language and ',' in primary_language:
        return primary_language

    primary_language = (primary_language or get_language() or 'en').split(',')[0]
    codes = []
    seen = set()

    if primary_language:
        codes.append(primary_language)
        seen.add(primary_language)

    for lang in Language.objects.all().order_by('language_name'):
        if lang.full_code not in seen:
            codes.append(lang.full_code)
            seen.add(lang.full_code)

    if not codes:
        codes = ['en']

    return ','.join(codes[:20])


def platform_language_codes():
    return platform_language_param().split(',')


def get_translated_geofeature_list(geofeature, country=None, is_primary=False):
    from bluebottle.utils.models import Language

    data = []
    current_language = geofeature._current_language
    country_language = country._current_language if country else None

    for lang in Language.objects.all():
        geofeature.set_current_language(lang.full_code)
        name = geofeature.name
        place_name = geofeature.place_name
        if not name and not place_name:
            continue

        entry = {
            'id': geofeature.pk,
            'name': name or '',
            'place_name': place_name or '',
            'language': lang.full_code,
            'feature_type': geofeature.feature_type or '',
            'is_primary': is_primary,
        }
        if country:
            country.set_current_language(lang.full_code)
            entry['country'] = country.name
            entry['country_code'] = country.alpha2_code
        data.append(entry)

    geofeature._current_language = current_language
    if country and country_language is not None:
        country._current_language = country_language
    return data


CARD_LOCATION_FEATURE_TYPES = {
    'address': 'address',
    'neighborhood': 'neighborhood',
    'locality': 'locality',
    'place': 'place',
    'region': 'region',
}


def _entry_value(entry, key, default=None):
    if entry is None:
        return default
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _entries_for_language(entries, language):
    language_entries = [
        entry for entry in entries
        if _entry_value(entry, 'language') == language
    ]
    if language_entries:
        return language_entries

    language_prefix = language.split('-')[0]
    return [
        entry for entry in entries
        if _entry_value(entry, 'language', '').startswith(language_prefix)
    ]


def _geofeatures_for_language(geofeatures, language):
    return _entries_for_language(geofeatures, language)


def _card_location_level_value(geofeatures, level):

    feature_type = CARD_LOCATION_FEATURE_TYPES.get(level)
    if not feature_type:
        return None

    feature = next(
        (
            geofeature for geofeature in geofeatures
            if _entry_value(geofeature, 'feature_type') == feature_type
        ),
        None,
    )
    return _entry_value(feature, 'name') if feature else None


CARD_LOCATION_MODES = frozenset({
    'neighbourhood',
    'neighbourhood_city',
    'city',
    'city_region',
    'city_country',
})


def _normalize_card_location_mode(card_location_display):
    if not card_location_display:
        return None
    if isinstance(card_location_display, (list, tuple)):
        return 'city_country'
    if isinstance(card_location_display, str) and ',' in card_location_display:
        return 'city_country'
    return card_location_display


def _first_present(*values):
    for value in values:
        if value:
            return value
    return None


def _join_parts(*values):
    parts = [value for value in values if value]
    return ', '.join(parts) if parts else None


def _country_for_card(full_name, code, abbreviate=False):
    if abbreviate:
        return code or full_name
    return full_name or code


def _get_card_location_country_name(geofeatures, activity, language):
    country_feature = next(
        (
            geofeature for geofeature in geofeatures
            if _entry_value(geofeature, 'feature_type') == 'country'
        ),
        None,
    )
    value = _entry_value(country_feature, 'name')
    if not value:
        value = next(
            (
                _entry_value(geofeature, 'country')
                for geofeature in geofeatures
                if _entry_value(geofeature, 'country')
            ),
            None,
        )
    if not value:
        countries = getattr(activity, 'country', None) or []
        language_countries = _entries_for_language(countries, language)
        if language_countries:
            value = _entry_value(language_countries[0], 'name')
    return value


def _get_card_location_country_code(geofeatures):
    return next(
        (
            _entry_value(geofeature, 'country_code')
            for geofeature in geofeatures
            if _entry_value(geofeature, 'country_code')
        ),
        None,
    )


def _get_card_location_parts(activity, language_geofeatures, language):
    place = _card_location_level_value(language_geofeatures, 'place')
    locality = _card_location_level_value(language_geofeatures, 'locality')
    city = _first_present(place, locality)
    return {
        'neighborhood': _card_location_level_value(language_geofeatures, 'neighborhood'),
        'locality': locality,
        'city': city,
        'region': _card_location_level_value(language_geofeatures, 'region'),
        'country': _get_card_location_country_name(
            language_geofeatures, activity, language
        ),
        'country_code': _get_card_location_country_code(language_geofeatures),
    }


def format_card_location_from_values(
    mode,
    *,
    neighborhood=None,
    locality=None,
    city=None,
    region=None,
    country=None,
    country_code=None,
):
    mode = _normalize_card_location_mode(mode)
    if not mode or mode not in CARD_LOCATION_MODES:
        return None

    parts = {
        'neighborhood': neighborhood,
        'locality': locality,
        'city': city,
        'region': region,
        'country': country,
        'country_code': country_code,
    }
    return _format_card_location_from_parts(mode, parts)


def _format_card_location_from_parts(mode, parts):
    country = parts.get('country')
    country_code = parts.get('country_code')

    if mode == 'neighbourhood':
        return _first_present(
            parts.get('neighborhood'),
            parts.get('city'),
            parts.get('region'),
            country,
            country_code,
        )

    if mode == 'neighbourhood_city':
        neighborhood = parts.get('neighborhood')
        locality = parts.get('locality')
        city = parts.get('city')
        if neighborhood and city:
            return _join_parts(neighborhood, city)
        if locality and city and locality != city:
            return _join_parts(locality, city)
        if city:
            return city
        if locality:
            return locality
        if neighborhood:
            return neighborhood
        return _first_present(
            parts.get('region'),
            _country_for_card(country, country_code, abbreviate=False),
            country_code,
        )

    if mode == 'city':
        return _first_present(
            parts.get('city'),
            parts.get('region'),
            country,
            country_code,
        )

    if mode == 'city_region':
        city = parts.get('city')
        region = parts.get('region')
        if city and region:
            return _join_parts(city, region)
        if region:
            return region
        return _country_for_card(country, country_code, abbreviate=False)

    if mode == 'city_country':
        city = parts.get('city')
        region = parts.get('region')
        if city and (country or country_code):
            return _join_parts(
                city,
                _country_for_card(country, country_code, abbreviate=True),
            )
        if region and (country or country_code):
            return _join_parts(
                region,
                _country_for_card(country, country_code, abbreviate=True),
            )
        return _country_for_card(country, country_code, abbreviate=False)

    return None


CARD_LOCATION_COMMON_LEVEL_CHECKS = {
    'neighbourhood': (
        ('neighborhood',),
        ('locality',),
        ('city',),
        ('region',),
        ('country',),
    ),
    'neighbourhood_city': (
        ('neighborhood', 'city'),
        ('locality', 'city'),
        ('city',),
        ('region',),
        ('country',),
    ),
    'city': (
        ('city',),
        ('region',),
        ('country',),
    ),
    'city_region': (
        ('city', 'region'),
        ('region',),
        ('country',),
    ),
    'city_country': (
        ('city', 'country'),
        ('region', 'country'),
        ('country',),
    ),
}


def _common_parts_for_keys(all_parts, keys):
    if not all_parts:
        return None

    merged = {
        'neighborhood': None,
        'locality': None,
        'city': None,
        'region': None,
        'country': None,
        'country_code': None,
    }

    for key in keys:
        if key == 'country':
            country_keys = [
                part.get('country_code') or part.get('country')
                for part in all_parts
            ]
            if any(not value for value in country_keys):
                return None
            if len(set(country_keys)) != 1:
                return None
            merged['country'] = all_parts[0].get('country')
            merged['country_code'] = all_parts[0].get('country_code')
        else:
            values = [part.get(key) for part in all_parts]
            if any(not value for value in values):
                return None
            if len(set(values)) != 1:
                return None
            merged[key] = values[0]

    return merged


def format_common_card_location(activity, card_location_display, language, location_parts):
    mode = _normalize_card_location_mode(card_location_display)
    if not mode or mode not in CARD_LOCATION_MODES:
        return None

    if not location_parts:
        return None

    if mode == 'neighbourhood_city':
        return _format_multi_neighbourhood_city(mode, location_parts)

    if mode == 'city_country':
        return _format_multi_city_country(mode, location_parts)

    level_checks = CARD_LOCATION_COMMON_LEVEL_CHECKS.get(mode, ())

    for keys in level_checks:
        common_parts = _common_parts_for_keys(location_parts, keys)
        if not common_parts:
            continue

        formatted = _format_card_location_from_parts(mode, common_parts)
        if formatted:
            return formatted

    return None


def _format_multi_neighbourhood_city(mode, location_parts):
    common_neighborhood_city = _common_parts_for_keys(
        location_parts, ('neighborhood', 'city')
    )
    if common_neighborhood_city:
        return _format_card_location_from_parts(mode, common_neighborhood_city)

    common_locality_city = _common_parts_for_keys(location_parts, ('locality', 'city'))
    if common_locality_city:
        return _format_card_location_from_parts(mode, common_locality_city)

    common_city = _common_parts_for_keys(location_parts, ('city',))
    if common_city:
        return _format_card_location_from_parts(mode, common_city)

    for keys in (('region',), ('country',)):
        common_parts = _common_parts_for_keys(location_parts, keys)
        if common_parts:
            formatted = _format_card_location_from_parts(mode, common_parts)
            if formatted:
                return formatted

    return None


def _format_multi_city_country(mode, location_parts):
    common_city_country = _common_parts_for_keys(location_parts, ('city', 'country'))
    if common_city_country:
        return _format_card_location_from_parts(mode, common_city_country)

    common_region_country = _common_parts_for_keys(location_parts, ('region', 'country'))
    if common_region_country:
        return _format_card_location_from_parts(mode, common_region_country)

    common_country = _common_parts_for_keys(location_parts, ('country',))
    if common_country:
        return _format_card_location_from_parts(mode, common_country)

    return None


def card_location_parts_from_geofeatures(activity, geofeatures, language):
    if not geofeatures:
        return None

    language_geofeatures = _geofeatures_for_language(geofeatures, language)
    if not language_geofeatures:
        return None

    return _get_card_location_parts(activity, language_geofeatures, language)


def card_location_parts_from_entry(entry):
    country = getattr(entry, 'country', None)
    country_name = None
    country_code = getattr(entry, 'country_code', None)
    if country is not None:
        country_name = getattr(country, 'name', country)
        if not country_code:
            country_code = getattr(country, 'alpha2_code', None)

    return {
        'neighborhood': None,
        'locality': getattr(entry, 'locality', None),
        'city': getattr(entry, 'locality', None),
        'region': None,
        'country': country_name,
        'country_code': country_code,
    }


def geofeatures_for_geolocation(geolocation):
    geofeatures = []
    primary_id = geolocation.geofeature_id
    country = geolocation.country
    for geofeature in geolocation.geofeatures.all():
        geofeatures.extend(get_translated_geofeature_list(
            geofeature,
            country=country,
            is_primary=geofeature.pk == primary_id,
        ))
    return geofeatures


def card_location_parts_for_geolocation(geolocation, language, activity=None):
    activity = activity or type('Activity', (), {'country': []})()
    geofeatures = geofeatures_for_geolocation(geolocation)
    parts = card_location_parts_from_geofeatures(activity, geofeatures, language)
    if parts:
        return parts

    country = geolocation.country
    return {
        'neighborhood': None,
        'locality': geolocation.locality,
        'city': geolocation.locality,
        'region': geolocation.province,
        'country': country.name if country else None,
        'country_code': country.alpha2_code if country else None,
    }


def format_multi_location_display(activity, card_location_display, language, geolocations):
    location_parts = [
        card_location_parts_for_geolocation(geolocation, language, activity)
        for geolocation in geolocations
    ]
    return format_common_card_location(
        activity,
        card_location_display,
        language,
        location_parts,
    )


def has_common_physical_address(geolocations, language):
    language = (language or get_language() or 'en').split(',')[0]
    name_maps = [
        geofeature_names_for_geolocation(geolocation, language)
        for geolocation in geolocations
    ]
    shared = collect_shared_geofeature_names(name_maps)
    return 'address' in shared or 'street' in shared


def format_multi_location_label(activity, card_location_display, language, geolocations):
    language = (language or get_language() or 'en').split(',')[0]
    street_address = common_formatted_address_for_geolocations(geolocations, language)
    card_address = format_multi_location_display(
        activity,
        card_location_display,
        language,
        geolocations,
    )

    if street_address and has_common_physical_address(geolocations, language):
        return street_address

    return card_address or street_address


def _geofeature_entry_name(entry):
    if isinstance(entry, dict):
        return entry.get('name') or entry.get('place_name')
    return getattr(entry, 'name', None) or getattr(entry, 'place_name', None)


def geofeature_names_from_entries(geofeatures, language):
    names = {}
    language_entries = _entries_for_language(geofeatures, language)

    for entry in language_entries:
        feature_type = _entry_value(entry, 'feature_type')
        name = _geofeature_entry_name(entry)
        if feature_type and name:
            names[feature_type] = name

    return names


def geolocation_fallback_names(geolocation):
    names = {}
    if geolocation.formatted_address:
        names['address'] = geolocation.formatted_address
    if geolocation.street:
        names['street'] = geolocation.street
    if geolocation.postal_code:
        names['postcode'] = geolocation.postal_code
    if geolocation.locality:
        names['place'] = geolocation.locality
    if geolocation.country:
        names['country'] = geolocation.country.name
    return names


def geofeature_names_for_geolocation(geolocation, language):
    names = {}

    for geofeature in geolocation.geofeatures.all():
        geofeature.set_current_language(language)
        feature_type = geofeature.feature_type
        if not feature_type:
            continue
        name = geofeature.name or geofeature.place_name
        if name:
            names[feature_type] = name

    for key, value in geolocation_fallback_names(geolocation).items():
        names.setdefault(key, value)

    return names


def collect_shared_geofeature_names(name_maps):
    if len(name_maps) < 2:
        return {}

    shared = {}
    for feature_type in FORMATTED_ADDRESS_HIERARCHY:
        values = [name_map.get(feature_type) for name_map in name_maps]
        if any(not value for value in values) or len(set(values)) != 1:
            continue
        shared[feature_type] = values[0]

    return shared


def format_shared_geofeature_address(shared):
    if not shared:
        return None

    if shared.get('address'):
        return shared['address']

    parts = []
    if shared.get('street'):
        parts.append(shared['street'])

    city = shared.get('place') or shared.get('locality')
    city_line = ' '.join(
        part for part in (shared.get('postcode'), city) if part
    )
    if city_line:
        parts.append(city_line)
    elif city:
        parts.append(city)

    if shared.get('region') and not city:
        parts.append(shared['region'])

    if shared.get('country'):
        parts.append(shared['country'])

    return ', '.join(parts) if parts else None


def common_formatted_address_for_geolocations(geolocations, language=None):
    language = (language or get_language() or 'en').split(',')[0]
    name_maps = [
        geofeature_names_for_geolocation(geolocation, language)
        for geolocation in geolocations
    ]
    return format_shared_geofeature_address(collect_shared_geofeature_names(name_maps))


def common_formatted_address_from_geofeatures(geofeature_groups, language=None):
    language = (language or get_language() or 'en').split(',')[0]
    name_maps = [
        geofeature_names_from_entries(geofeatures, language)
        for geofeatures in geofeature_groups
    ]
    return format_shared_geofeature_address(collect_shared_geofeature_names(name_maps))


def format_card_location(activity, card_location_display, language, geofeatures=None):
    mode = _normalize_card_location_mode(card_location_display)
    if not mode or mode not in CARD_LOCATION_MODES:
        return None

    if geofeatures is None:
        geofeatures = getattr(activity, 'geofeature', None)
    if not geofeatures:
        return None

    language_geofeatures = _geofeatures_for_language(geofeatures, language)
    if not language_geofeatures:
        return None

    parts = _get_card_location_parts(activity, language_geofeatures, language)
    return _format_card_location_from_parts(mode, parts)


def iter_geofeature_data(feature, language=None):
    properties = feature.get('properties', {})
    context = properties.get('context', {})
    if not isinstance(context, dict):
        context = {}

    primary_type = properties.get('feature_type', '')
    primary_name = properties.get('name_preferred') or properties.get('name', '')

    yield {
        'mapbox_id': properties.get('mapbox_id'),
        'feature_type': primary_type,
        'place_name': geofeature_place_name(
            primary_type,
            primary_name,
            context,
            full_address=properties.get('full_address'),
            language=language,
        ),
        'name': primary_name,
        'translations': properties.get('translations', {}),
        'context': context,
    }

    for feature_type in CONTEXT_TYPES:
        context_data = context.get(feature_type)
        if not context_data or not context_data.get('mapbox_id'):
            continue

        if context_data.get('mapbox_id') == properties.get('mapbox_id'):
            continue

        context_name = context_data.get('name', '')
        yield {
            'mapbox_id': context_data['mapbox_id'],
            'feature_type': feature_type,
            'place_name': geofeature_place_name(
                feature_type, context_name, context, language=language
            ),
            'name': context_name,
            'translations': context_data.get('translations', {}),
            'context': context,
        }


def parse_feature(feature):
    if not feature:
        return {}

    properties = feature.get('properties', {})
    context = properties.get('context', {})
    if not isinstance(context, dict):
        context = {}

    address_context = context.get('address', {})
    country_context = context.get('country', {})

    country_code = country_context.get('country_code', '')
    if country_code:
        country_code = country_code.upper()

    return {
        'mapbox_id': properties.get('mapbox_id'),
        'formatted_address': feature_place_name(properties),
        'street': address_context.get('street_name') or properties.get('name', ''),
        'street_number': address_context.get('address_number', ''),
        'postal_code': context.get('postcode', {}).get('name', ''),
        'locality': (
            context.get('place', {}).get('name')
            or context.get('locality', {}).get('name')
            or ''
        ),
        'province': context.get('region', {}).get('name', ''),
        'country_code': country_code,
    }


def apply_parsed_feature(geolocation, parsed):
    if not parsed:
        return

    if parsed.get('mapbox_id'):
        geolocation.mapbox_id = parsed['mapbox_id']
    if parsed.get('formatted_address'):
        geolocation.formatted_address = parsed['formatted_address'][:255]
    if parsed.get('street'):
        geolocation.street = parsed['street'][:255]
    if parsed.get('street_number'):
        geolocation.street_number = parsed['street_number'][:255]
    if parsed.get('postal_code'):
        geolocation.postal_code = parsed['postal_code'][:255]
    if parsed.get('locality'):
        geolocation.locality = parsed['locality'][:255]
    if parsed.get('province'):
        geolocation.province = parsed['province'][:255]

    country_code = parsed.get('country_code')
    if country_code:
        from bluebottle.geo.models import Country
        country = Country.objects.filter(alpha2_code=country_code).first()
        if country:
            geolocation.country = country


def _apply_geofeature_translations(geofeature, data, primary_language):
    feature_type = data.get('feature_type', '')
    context = data.get('context', {})
    name = (data.get('name') or '')[:5000]
    place_name = (data.get('place_name') or '')[:5000]

    if place_name or name:
        geofeature.set_current_language(primary_language)
        if place_name:
            geofeature.place_name = place_name
        if name:
            geofeature.name = name
        geofeature.save()

    translations = data.get('translations', {})
    for lang_code, translation in translations.items():
        if not isinstance(translation, dict):
            continue

        if lang_code == primary_language:
            continue

        translated_name = (translation.get('name') or name)[:5000]
        translated_place_name = translation_place_name(
            feature_type,
            name,
            context,
            translation=translation,
            language=lang_code,
        )[:5000]
        if not translated_name and not translated_place_name:
            continue

        geofeature.set_current_language(lang_code)
        if translated_place_name:
            geofeature.place_name = translated_place_name
        if translated_name:
            geofeature.name = translated_name
        geofeature.save()


def select_primary_geofeature(geolocation):
    from bluebottle.geo.models import GeoFeature

    if not geolocation.mapbox_id:
        return None

    return GeoFeature.objects.filter(mapbox_id=geolocation.mapbox_id).first()


def _sync_geofeature_records(geolocation, feature, primary_language):
    from bluebottle.geo.models import GeoFeature

    geofeature_ids = []

    for data in iter_geofeature_data(feature, language=primary_language):
        mapbox_id = data.get('mapbox_id')
        if not mapbox_id:
            continue

        geofeature, created = GeoFeature.objects.get_or_create(
            mapbox_id=mapbox_id,
            defaults={
                'feature_type': data.get('feature_type', ''),
            },
        )

        feature_type = data.get('feature_type', '')
        if feature_type and geofeature.feature_type != feature_type:
            geofeature.feature_type = feature_type
            geofeature.save(update_fields=['feature_type'])

        _apply_geofeature_translations(geofeature, data, primary_language)

        if geofeature.pk not in geofeature_ids:
            geofeature_ids.append(geofeature.pk)

    return geofeature_ids


def sync_geofeatures(geolocation, feature, language=None):
    from bluebottle.geo.models import Geolocation

    primary_language = (language or get_language() or 'en').split(',')[0]
    geofeature_ids = _sync_geofeature_records(
        geolocation, feature, primary_language
    )

    if geolocation.pk:
        geolocation.geofeatures.set(geofeature_ids)
        primary_geofeature = select_primary_geofeature(geolocation)
        Geolocation.objects.filter(pk=geolocation.pk).update(geofeature=primary_geofeature)
        geolocation.geofeature = primary_geofeature
