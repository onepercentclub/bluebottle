"""
GeoFeature collection and upsert logic (Mapbox v6 context hierarchy → GeoFeature rows).
"""
from __future__ import annotations

import requests
from django.conf import settings
from django.db import IntegrityError

from bluebottle.geo.geolocation import sync_geolocation_country
from bluebottle.geo.mapbox import V6_FORWARD_URL
from bluebottle.geo.models import GeoFeature, Geolocation
from bluebottle.utils.models import Language

try:
    from addressformatting import AddressFormatter
except ImportError:  # pragma: no cover
    AddressFormatter = None


def _get_ctx_name(ctx, language):
    """Return a localized name from a Mapbox v6 context object."""
    translated = (ctx.get('translations') or {}).get(language) or {}
    return translated.get('name') or ctx.get('name')


def _normalize_country_code(code):
    if not code:
        return None
    code = str(code).strip()
    if '-' in code:
        code = code.split('-', 1)[0]
    if len(code) == 2:
        return code.upper()
    return code


def _build_address_dict(place_type, feature, props, language):
    """Map a Mapbox feature + context hierarchy to addressformatting field names."""
    context = props.get('context') or feature.get('context') or {}
    country_ctx = context.get('country') or {}
    country_name = _get_ctx_name(country_ctx, language) if country_ctx else None
    street_name = _get_ctx_name(context.get('street') or {}, language) if context.get('street') else None
    neighbourhood_name = (
        _get_ctx_name(context.get('neighborhood') or {}, language) if context.get('neighborhood') else None
    )
    district_name = _get_ctx_name(context.get('district') or {}, language) if context.get('district') else None
    region_name = _get_ctx_name(context.get('region') or {}, language) if context.get('region') else None
    city_name = _get_ctx_name(context.get('place') or {}, language) if context.get('place') else None
    postcode_name = _get_ctx_name(context.get('postcode') or {}, language) if context.get('postcode') else None

    translated = (feature.get('translations') or {}).get(language) or {}
    name = translated.get('name') or feature.get('text') or props.get('name')

    if place_type in ('address', 'secondary_address'):
        house_number = props.get('address_number') or feature.get('address') or props.get('address')
        if street_name and house_number and str(house_number) not in str(street_name):
            road = street_name
        else:
            road = name
            house_number = None
        return {
            'house_number': house_number,
            'road': road,
            'city': city_name,
            'postcode': postcode_name,
            'state': region_name,
            'country': country_name,
        }
    if place_type in ('neighborhood',):
        return {
            'road': neighbourhood_name,
            'city': city_name,
            'state': region_name,
            'country': country_name,
        }
    if place_type in ('district',):
        return {
            'road': district_name,
            'city': city_name,
            'state': region_name,
            'country': country_name,
        }
    if place_type in ('locality',):
        return {
            'road': name,
            'city': city_name,
            'state': region_name,
            'country': country_name,
        }
    if place_type in ('street',):
        return {
            'road': name,
            'city': city_name,
            'region': region_name,
            'country': country_name,
        }
    if place_type in ('place',):
        return {
            'city': name,
            'state': region_name,
            'region': region_name,
            'country': country_name,
        }
    if place_type == 'region':
        return {
            'state': name,
            'country': country_name,
        }
    if place_type == 'country':
        return {
            'country': name,
        }
    if place_type == 'postcode':
        return {
            'postcode': name,
            'city': city_name,
            'state': region_name,
            'country': country_name,
        }
    return {}


def _format_address_fallback(address):
    """Join address parts when addressformatting is unavailable or fails."""
    road = address.get('road')
    house_number = address.get('house_number')
    if road and house_number and str(house_number) not in str(road):
        road_part = f'{road} {house_number}'.strip()
    else:
        road_part = road or house_number

    parts = []
    for value in (
        road_part,
        address.get('postcode'),
        address.get('city'),
        address.get('state') or address.get('region'),
        address.get('country'),
    ):
        if value and (not parts or parts[-1] != value):
            parts.append(str(value))
    return ', '.join(parts) or None


def format_place_name(place_type, feature, props, language, formatter=None):
    """Build a one-line locale-aware place name for GeoFeature.place_name."""
    context = props.get('context') or feature.get('context') or {}
    country_ctx = context.get('country') or {}
    country_code = _normalize_country_code(
        country_ctx.get('country_code')
        or country_ctx.get('short_code')
        or props.get('short_code')
    )

    address = {k: v for k, v in _build_address_dict(place_type, feature, props, language).items() if v}
    if not address:
        return None

    if formatter is None and AddressFormatter is not None:
        formatter = AddressFormatter()

    if formatter is not None:
        try:
            formatted = formatter.one_line(address, country=country_code)
            if formatted and formatted.strip():
                return formatted.strip()
        except Exception:
            pass

    return _format_address_fallback(address)


def _resolve_place_name(place_type, feature, props, language, formatter, text_value):
    """Pick GeoFeature.place_name: formatted line, then Mapbox full address, then name."""
    formatted = format_place_name(place_type, feature, props, language, formatter=formatter)
    if formatted and formatted != text_value:
        return formatted

    if place_type in ('address', 'secondary_address'):
        for key in ('full_address', 'place_formatted'):
            value = props.get(key)
            if value:
                return value

    return (
        formatted
        or props.get('full_address')
        or feature.get('place_name')
        or props.get('place_formatted')
        or text_value
    )


def _clear_geo_feature_translation_cache(geo_feature):
    """Clear parler's in-memory translation cache after GeoFeature rows are updated in bulk."""
    if geo_feature._translations_cache is not None:
        geo_feature._translations_cache.clear()


def resolve_geo_feature(*, mapbox_id, defaults=None):
    """Return one GeoFeature for mapbox_id, merging duplicate rows if present.

    Used by collect_geo_features when upserting context hierarchy rows.
    """
    defaults = defaults or {}
    matches = list(GeoFeature.objects.filter(mapbox_id=mapbox_id).order_by('pk'))
    if not matches:
        return GeoFeature.objects.create(mapbox_id=mapbox_id, **defaults), True

    canonical = matches[0]
    translation_model = canonical._parler_meta.root.model
    for duplicate in matches[1:]:
        for geolocation in Geolocation.objects.filter(features=duplicate):
            geolocation.features.remove(duplicate)
            geolocation.features.add(canonical)

        for trans in translation_model.objects.filter(master_id=duplicate.pk):
            translation_model.objects.get_or_create(
                master_id=canonical.pk,
                language_code=trans.language_code,
                defaults={
                    'name': trans.name,
                    'place_name': trans.place_name,
                },
            )

        duplicate.delete()

    if len(matches) > 1:
        canonical = GeoFeature.objects.get(pk=canonical.pk)

    return canonical, False


def _upsert_geo_feature_translations(geo_feature, language_values):
    """Create or update parler translation rows (name, place_name) for one GeoFeature."""
    translation_model = geo_feature._parler_meta.root.model
    for language_code, name, place_name in language_values:
        defaults = {
            'name': name,
            'place_name': place_name or name,
        }
        try:
            translation_model.objects.update_or_create(
                master_id=geo_feature.pk,
                language_code=language_code,
                defaults=defaults,
            )
        except IntegrityError:
            translation_model.objects.filter(
                master_id=geo_feature.pk,
                language_code=language_code,
            ).update(**defaults)
    _clear_geo_feature_translation_cache(geo_feature)


def _update_geo_feature_fields(geo_feature, **fields):
    """Bulk-update scalar GeoFeature columns without a full model save."""
    if not fields:
        return
    GeoFeature.objects.filter(pk=geo_feature.pk).update(**fields)
    for field, value in fields.items():
        setattr(geo_feature, field, value)
    _clear_geo_feature_translation_cache(geo_feature)


def _feature_props_from_context(ctx, context, selected_props=None):
    """Build Mapbox-like properties for a context slice, inheriting root feature fields."""
    selected_props = selected_props or {}
    props = {
        'short_code': ctx.get('short_code') or ctx.get('country_code'),
        'context': context,
    }
    for key in ('full_address', 'place_formatted', 'address_number', 'address'):
        value = selected_props.get(key)
        if value:
            props[key] = value
    return props


def collect_geo_features(geolocation):
    """Fetch Mapbox v6 context for a geolocation, upsert GeoFeature rows, and link them.

    Called from sync_geolocation_after_save when mapbox_id is set or changed.
    Returns the number of GeoFeatures linked to the geolocation.
    """
    if not geolocation.mapbox_id:
        return 0

    current_place_type = geolocation.mapbox_id.split('.')[0]
    languages = list(dict.fromkeys(Language.objects.values_list('code', flat=True)))
    formatter = AddressFormatter() if AddressFormatter else None

    def upsert_feature(feature, force_place_type=None, force_update=False):
        """Create or update one GeoFeature from a Mapbox feature dict; return (geo_feature, created)."""
        props = feature.get('properties') or {}
        mapbox_id = feature.get('id') or props.get('mapbox_id')
        if not mapbox_id:
            return None, False
        place_type = (
            force_place_type
            or (feature.get('place_type') or [None])[0]
            or props.get('feature_type')
            or current_place_type
        )

        geo_feature, created = resolve_geo_feature(
            mapbox_id=mapbox_id,
            defaults={
                'code': props.get('short_code'),
                'place_type': place_type,
            },
        )
        _clear_geo_feature_translation_cache(geo_feature)

        field_updates = {}
        if geo_feature.place_type != place_type:
            field_updates['place_type'] = place_type
        short_code = props.get('short_code')
        if short_code and geo_feature.code != short_code:
            field_updates['code'] = short_code
        _update_geo_feature_fields(geo_feature, **field_updates)

        if created or force_update:
            translations = feature.get('translations') or {}
            language_values = []
            for language in languages:
                translated = translations.get(language) or {}
                text_value = (
                    translated.get('name')
                    or feature.get('text')
                    or props.get('name')
                    or props.get('place_formatted')
                    or props.get('full_address')
                )
                place_name_value = _resolve_place_name(
                    place_type, feature, props, language, formatter, text_value,
                )
                language_values.append((
                    language,
                    text_value,
                    place_name_value or text_value,
                ))
            _upsert_geo_feature_translations(geo_feature, language_values)

        return geo_feature, created

    response = requests.get(
        V6_FORWARD_URL,
        params={
            'q': geolocation.mapbox_id,
            'access_token': settings.MAPBOX_API_KEY,
            'permanent': 'true',
            'language': ','.join(languages),
            'limit': 1,
        },
        timeout=30,
    )
    response.raise_for_status()
    features = (response.json() or {}).get('features') or []
    if not features:
        return 0

    selected = features[0]
    selected_props = selected.get('properties') or {}
    context = selected_props.get('context') or {}
    created_or_linked = 0
    linked_ids = set()

    def link_feature(geo_feature):
        nonlocal created_or_linked
        if not geo_feature or geo_feature.pk in linked_ids:
            return
        geolocation.features.add(geo_feature)
        linked_ids.add(geo_feature.pk)
        created_or_linked += 1

    primary_type = (
        selected_props.get('feature_type')
        or (selected.get('place_type') or [None])[0]
        or current_place_type
    )
    primary_feature = {
        **selected,
        'properties': selected_props,
        'context': context,
    }
    geo_feature, _created = upsert_feature(
        primary_feature, force_place_type=primary_type, force_update=True,
    )
    link_feature(geo_feature)

    primary_id = selected.get('id') or selected_props.get('mapbox_id')

    for place_type in context.keys():
        ctx = context.get(place_type)
        if not ctx:
            continue

        ctx_id = ctx.get('mapbox_id')
        if ctx_id and ctx_id == primary_id:
            continue

        ctx_feature = {
            'id': ctx_id,
            'place_type': [place_type],
            'text': ctx.get('name'),
            'place_name': ctx.get('name'),
            'translations': ctx.get('translations') or {},
            'context': context,
            'properties': {
                **_feature_props_from_context(ctx, context, selected_props),
                'feature_type': place_type,
            },
        }
        geo_feature, _created = upsert_feature(
            ctx_feature, force_place_type=place_type, force_update=True,
        )
        link_feature(geo_feature)

    sync_geolocation_country(geolocation, context=context, mapbox_feature=selected)

    return created_or_linked
