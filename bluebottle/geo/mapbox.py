import requests

from django.conf import settings
from django.utils.translation import get_language

MAPBOX_GEOCODE_V6_BASE = 'https://api.mapbox.com/search/geocode/v6'

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


def is_v6_mapbox_id(value):
    return bool(value and value.startswith('dXJuOm1ie'))


def geocode_request(path, params):
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


def first_feature(response):
    features = response.get('features', [])
    return features[0] if features else None


def platform_language_param():
    from bluebottle.utils.models import Language

    return ','.join(
        language.full_code for language in Language.objects.all()
    ) or 'en'


def lookup_by_mapbox_id(mapbox_id, language=None):
    return geocode_request('/forward', {
        'q': mapbox_id,
        'limit': 1,
        'language': platform_language_param(),
    })


def _language_keys(language):
    """Mapbox and parler may use `en` or `en-GB`; try both."""
    if not language:
        return
    yield language
    base = language.split('-')[0]
    if base != language:
        yield base


def _translated_field(data, field, language, default=''):
    translations = (data or {}).get('translations') or {}
    for key in _language_keys(language):
        entry = translations.get(key)
        if isinstance(entry, dict) and entry.get(field):
            return entry[field]
    return default


def _context_name(context, feature_type, language=None):
    data = (context or {}).get(feature_type) or {}
    if not data:
        return ''
    if language:
        localized = _translated_field(data, 'name', language)
        if localized:
            return localized
        if data.get('translations'):
            # Translations exist but not for this language — avoid mixing
            # e.g. "Den Haag" + "Netherlands".
            return ''
    return data.get('name', '') or ''


def _feature_name_for_language(data, language, fallback_name=''):
    translated = _translated_field(data, 'name', language)
    if translated:
        return translated.strip()
    if language:
        # Prefer leaving name empty over mixing languages; caller may skip.
        return (fallback_name or '').strip()
    return (fallback_name or data.get('name') or '').strip()


def geofeature_place_name(feature_type, name, context=None, full_address=None, language=None):
    """Build a display place_name for a Mapbox feature / context entry."""
    context = context if isinstance(context, dict) else {}
    name = (name or '').strip()

    if feature_type == 'address':
        if full_address:
            return full_address.strip()
        if not name:
            return ''
        postcode = _context_name(context, 'postcode', language)
        city = (
            _context_name(context, 'place', language)
            or _context_name(context, 'locality', language)
        )
        country = _context_name(context, 'country', language)
        locality = ' '.join(part for part in (postcode, city) if part)
        return ', '.join(part for part in (name, locality, country) if part)

    if not name:
        return (full_address or '').strip()
    if feature_type == 'country':
        return name

    country = _context_name(context, 'country', language)
    if feature_type in ('region', 'place', 'locality'):
        return ', '.join(part for part in (name, country) if part)

    city = (
        _context_name(context, 'place', language)
        or _context_name(context, 'locality', language)
    )
    return ', '.join(part for part in (name, city, country) if part)


def iter_geofeature_data(feature, language=None):
    properties = feature.get('properties', {})
    context = properties.get('context', {})
    if not isinstance(context, dict):
        context = {}

    primary_type = properties.get('feature_type', '')
    primary_fallback = properties.get('name_preferred') or properties.get('name', '')
    primary_name = _feature_name_for_language(
        properties, language, fallback_name=primary_fallback
    ) or primary_fallback

    translated_address = (
        _translated_field(properties, 'place_name', language)
        or _translated_field(properties, 'full_address', language)
    )
    # Only reuse the default full_address when no language was requested;
    # otherwise rebuild from context translations.
    address_full = translated_address or (
        None if language else properties.get('full_address')
    )

    yield {
        'mapbox_id': properties.get('mapbox_id'),
        'feature_type': primary_type,
        'place_name': geofeature_place_name(
            primary_type,
            primary_name,
            context,
            full_address=address_full,
            language=language,
        ),
        'name': primary_name,
        'translations': properties.get('translations', {}),
        'context': context,
        'full_address': properties.get('full_address'),
    }

    for feature_type in FEATURE_TYPE_HIERARCHY:
        context_data = context.get(feature_type)
        if not context_data or not context_data.get('mapbox_id'):
            continue
        if context_data.get('mapbox_id') == properties.get('mapbox_id'):
            continue

        context_fallback = context_data.get('name', '')
        context_name = _feature_name_for_language(
            context_data, language, fallback_name=context_fallback
        ) or context_fallback
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


def _set_geofeature_translation(geofeature, language, name, place_name):
    if not name and not place_name:
        return
    geofeature.set_current_language(language)
    if place_name:
        geofeature.place_name = place_name
    if name:
        geofeature.name = name
    geofeature.save()


def _platform_language_codes(primary_language=None):
    from bluebottle.utils.models import Language

    codes = []
    for language in Language.objects.all():
        if language.full_code not in codes:
            codes.append(language.full_code)
    if primary_language and primary_language not in codes:
        codes.insert(0, primary_language)
    return codes or ([primary_language] if primary_language else ['en'])


def _apply_geofeature_translations(geofeature, data, primary_language):
    feature_type = data.get('feature_type', '')
    context = data.get('context', {})
    fallback_name = (data.get('name') or '')[:5000]
    primary_keys = set(_language_keys(primary_language))
    has_named_translations = bool(data.get('translations'))

    for lang_code in _platform_language_codes(primary_language):
        name_from_translation = _translated_field(data, 'name', lang_code)
        address_from_translation = (
            _translated_field(data, 'place_name', lang_code)
            or _translated_field(data, 'full_address', lang_code)
        )
        is_primary = lang_code in primary_keys or any(
            key in primary_keys for key in _language_keys(lang_code)
        )

        if (
            not name_from_translation
            and not address_from_translation
            and has_named_translations
            and not is_primary
            and feature_type != 'address'
        ):
            # Skip incomplete languages rather than mixing a local name with
            # translated context ("Den Haag, Netherlands"). Addresses always
            # rebuild place_name from context when Mapbox omits a translation.
            continue

        translated_name = (name_from_translation or fallback_name)[:5000]
        if not translated_name:
            continue

        # Only pass Mapbox's address string when it is language-specific.
        # Never reuse the default full_address for other languages.
        full_address = address_from_translation if feature_type == 'address' else None

        translated_place_name = geofeature_place_name(
            feature_type,
            translated_name,
            context,
            full_address=full_address,
            language=lang_code,
        )[:5000]

        _set_geofeature_translation(
            geofeature, lang_code, translated_name, translated_place_name
        )


def select_primary_geofeature(geolocation):
    from bluebottle.geo.models import GeoFeature

    if not geolocation.mapbox_id:
        return None
    return GeoFeature.objects.filter(mapbox_id=geolocation.mapbox_id).first()


def country_code_from_feature(feature):
    """ISO alpha-2 from Mapbox feature context (e.g. NL)."""
    properties = (feature or {}).get('properties') or {}
    context = properties.get('context') or {}
    if not isinstance(context, dict):
        return ''
    country = context.get('country') or {}
    code = (country.get('country_code') or properties.get('country_code') or '')
    return code.upper() if code else ''


def apply_country_from_feature(geolocation, feature, overwrite=False):
    """
    Set geolocation.country from Mapbox context.country.country_code.

    By default only fills when country is empty (backoffice add / unset).
    """
    from bluebottle.geo.models import Country, Geolocation

    if geolocation.country_id and not overwrite:
        return geolocation.country

    country_code = country_code_from_feature(feature)
    if not country_code:
        return geolocation.country

    country = Country.objects.filter(alpha2_code=country_code).first()
    if not country:
        return geolocation.country

    if geolocation.pk:
        Geolocation.objects.filter(pk=geolocation.pk).update(country=country)
    geolocation.country = country
    return country


def sync_geofeatures(geolocation, feature, language=None):
    """Create/update GeoFeature rows from a Mapbox feature and link them."""
    from bluebottle.geo.models import GeoFeature, Geolocation

    primary_language = (language or get_language() or 'en').split(',')[0]
    geofeature_ids = []

    for data in iter_geofeature_data(feature, language=primary_language):
        mapbox_id = data.get('mapbox_id')
        if not mapbox_id:
            continue

        geofeature, _created = GeoFeature.objects.get_or_create(
            mapbox_id=mapbox_id,
            defaults={'feature_type': data.get('feature_type', '')},
        )

        feature_type = data.get('feature_type', '')
        if feature_type and geofeature.feature_type != feature_type:
            geofeature.feature_type = feature_type
            geofeature.save(update_fields=['feature_type'])

        _apply_geofeature_translations(geofeature, data, primary_language)

        if geofeature.pk not in geofeature_ids:
            geofeature_ids.append(geofeature.pk)

    if geolocation.pk:
        geolocation.geofeatures.set(geofeature_ids)
        primary = select_primary_geofeature(geolocation)
        apply_country_from_feature(geolocation, feature)
        Geolocation.objects.filter(pk=geolocation.pk).update(geofeature=primary)
        geolocation.geofeature = primary


def sync_geolocation(geolocation, language=None, feature=None):
    """
    Look up Mapbox data for geolocation.mapbox_id and store GeoFeatures.

    Safe to call from Geolocation.save(); ignores non-v6 ids and request errors.
    """
    if not geolocation.mapbox_id or not is_v6_mapbox_id(geolocation.mapbox_id):
        return

    try:
        if feature is None:
            feature = first_feature(
                lookup_by_mapbox_id(geolocation.mapbox_id, language=language)
            )
        if feature:
            sync_geofeatures(geolocation, feature, language=language)
    except requests.RequestException:
        pass
