import requests
from django.conf import settings
from django.utils.translation import get_language

from bluebottle.initiatives.models import ActivityCardLocationChoices

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAPBOX_GEOCODE_V6_BASE = 'https://api.mapbox.com/search/geocode/v6'

# Most specific → least specific. Used for address formatting and GeoFeature ordering.
FEATURE_TYPE_HIERARCHY = (
    'address',
    'street',
    'postcode',
    'neighborhood',
    'locality',
    'place',
    'district',
    'region',
    'country',
)

GEOFEATURE_TYPE_RANK = {
    feature_type: rank
    for rank, feature_type in enumerate(FEATURE_TYPE_HIERARCHY)
}


# ---------------------------------------------------------------------------
# HTTP / lookup
# ---------------------------------------------------------------------------

def is_v6_mapbox_id(value):
    return bool(value and value.startswith('dXJu'))


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


def platform_language_param():
    from bluebottle.utils.models import Language

    return ','.join(
        language.full_code for language in Language.objects.all()
    ) or 'en'


def lookup_by_mapbox_id(mapbox_id, language=None):
    return _request('/forward', {
        'q': mapbox_id,
        'limit': 1,
        'language': platform_language_param(),
    })


# ---------------------------------------------------------------------------
# Place-name helpers to set a full name on GeoFeature
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Display / translations for indexing and cards
# ---------------------------------------------------------------------------

def get_translated_geofeature_list(geofeature, country=None, is_primary=False):
    from bluebottle.utils.models import Language

    data = []
    current_language = geofeature._current_language
    country_language = country._current_language if country else None

    for lang in Language.objects.all():
        if not geofeature.has_translation(lang.full_code):
            continue

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
        if country and country.has_translation(lang.full_code):
            country.set_current_language(lang.full_code)
            entry['country'] = country.name
            entry['country_code'] = country.alpha2_code
        data.append(entry)

    geofeature._current_language = current_language
    if country and country_language is not None:
        country._current_language = country_language
    return data


def _entry_value(entry, key, default=None):
    if entry is None:
        return default
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _entries_for_language(entries, language):
    if not isinstance(language, str):
        language = 'en'

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


def _card_location_level_value(geofeatures, level):
    if level not in [
        'address',
        'neighborhood',
        'locality',
        'place',
        'region',
    ]:
        return None

    feature = next(
        (
            geofeature for geofeature in geofeatures
            if _entry_value(geofeature, 'feature_type') == level
        ),
        None,
    )
    return _entry_value(feature, 'name') if feature else None


CARD_LOCATION_MODES = ActivityCardLocationChoices.values


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
        value = _entry_value(country_feature, 'place_name')
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
    country_feature = next(
        (
            geofeature for geofeature in geofeatures
            if _entry_value(geofeature, 'feature_type') == 'country'
        ),
        None,
    )
    value = _entry_value(country_feature, 'country_code')
    if value:
        return value

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
    if mode not in CARD_LOCATION_MODES:
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
            values = [part.get(key) for part in all_parts if part]
            if any(not value for value in values):
                return None
            if len(set(values)) != 1:
                return None
            merged[key] = values[0]

    return merged


def format_common_card_location(activity, card_location_display, language, location_parts):
    if card_location_display not in CARD_LOCATION_MODES:
        return None
    mode = card_location_display

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
        return _country_for_card(
            common_country.get('country'),
            common_country.get('country_code'),
            abbreviate=False,
        )

    return None


def card_location_parts_from_geofeatures(activity, geofeatures, language):
    if not geofeatures:
        return None

    language_geofeatures = _entries_for_language(geofeatures, language)
    if not language_geofeatures:
        return None

    return _get_card_location_parts(activity, language_geofeatures, language)


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


def locality_from_geolocation(geolocation):
    if not geolocation:
        return None

    primary = geolocation.geofeature
    if primary and primary.feature_type in ('place', 'locality'):
        return primary.name

    for geofeature in geolocation.geofeatures.all():
        if geofeature.feature_type in ('place', 'locality'):
            return geofeature.name

    return None


def formatted_address_from_geolocation(geolocation):
    if not geolocation:
        return None

    for geofeature in geolocation.geofeatures.all():
        if geofeature.feature_type == 'address':
            return geofeature.place_name or geofeature.name

    primary = geolocation.geofeature
    if primary:
        return primary.place_name or primary.name

    return None


def card_location_for_geolocation(geolocation, language=None, activity=None):
    language = (language or get_language() or 'en').split(',')[0]
    activity = activity or type('Activity', (), {'country': []})()
    from bluebottle.initiatives.models import InitiativePlatformSettings

    mode = InitiativePlatformSettings.load().card_location_display
    return format_card_location(
        activity,
        mode,
        language,
        geofeatures=geofeatures_for_geolocation(geolocation),
    )


def card_location_parts_for_geolocation(geolocation, language, activity=None):
    activity = activity or type('Activity', (), {'country': []})()
    geofeatures = geofeatures_for_geolocation(geolocation)
    return card_location_parts_from_geofeatures(activity, geofeatures, language)


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

    return names


def collect_shared_geofeature_names(name_maps):
    if len(name_maps) < 2:
        return {}

    shared = {}
    for feature_type in FEATURE_TYPE_HIERARCHY:
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
    if card_location_display not in CARD_LOCATION_MODES:
        return None
    mode = card_location_display

    if geofeatures is None:
        geofeatures = getattr(activity, 'geofeature', None)
    if not geofeatures:
        return None

    language_geofeatures = _entries_for_language(geofeatures, language)
    if not language_geofeatures:
        return None

    parts = _get_card_location_parts(activity, language_geofeatures, language)
    return _format_card_location_from_parts(mode, parts)


# ---------------------------------------------------------------------------
# Sync Mapbox feature → GeoFeature records
# ---------------------------------------------------------------------------

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

    for feature_type in FEATURE_TYPE_HIERARCHY:
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
