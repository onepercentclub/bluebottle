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

GEOFEATURE_TYPE_RANK = {
    feature_type: rank
    for rank, feature_type in enumerate(reversed(CONTEXT_TYPES))
}

HOUSE_NUMBER_PATTERN = re.compile(r'^(\d+[a-zA-Z\-/]*)')


def is_v6_mapbox_id(value):
    return bool(value and value.startswith('dXJu'))


def needs_mapbox_id(value):
    return not value or value in ('', 'unknown') or not is_v6_mapbox_id(value)


def extract_housenumber(geolocation):
    if geolocation.street_number:
        return geolocation.street_number

    if geolocation.formatted_address:
        match = HOUSE_NUMBER_PATTERN.search(geolocation.formatted_address.strip())
        if match:
            return match.group(1)

    if geolocation.street:
        match = HOUSE_NUMBER_PATTERN.search(geolocation.street.strip())
        if match:
            return match.group(1)

    return None


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
    try:
        response = reverse_v6(
            longitude,
            latitude,
            types='address',
            language=language,
            limit=1,
        )
        feature = _prefer_address_feature(response)
        if feature:
            return feature
    except requests.RequestException as error:
        logger.warning('Mapbox reverse geocode (address) failed: %s', error)

    try:
        response = reverse_v6(longitude, latitude, language=language)
        return _prefer_address_feature(response)
    except requests.RequestException as error:
        logger.warning('Mapbox reverse geocode failed: %s', error)
        return None


def lookup_by_mapbox_id(mapbox_id, language=None):
    return forward_v6(query=mapbox_id, language=language)


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
            'language': language,
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
                language=language,
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
            language=language,
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


def iter_geofeature_data(feature):
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
            'place_name': geofeature_place_name(feature_type, context_name, context),
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


def sync_geofeatures(geolocation, feature, language=None):
    from bluebottle.geo.models import GeoFeature

    language = language or get_language() or 'en'
    geofeature_ids = []

    for data in iter_geofeature_data(feature):
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

        context = data.get('context', {})
        name = (data.get('name') or '')[:5000]
        place_name = (data.get('place_name') or '')[:5000]
        if place_name or name:
            geofeature.set_current_language(language)
            if place_name:
                geofeature.place_name = place_name
            if name:
                geofeature.name = name
            geofeature.save()

        translations = data.get('translations', {})
        for lang_code, translation in translations.items():
            if not isinstance(translation, dict):
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

        geofeature_ids.append(geofeature.pk)

    if geolocation.pk:
        geolocation.geofeatures.set(geofeature_ids)
