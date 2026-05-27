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


def _clear_geo_feature_translation_cache(geo_feature):
    if geo_feature._translations_cache is not None:
        geo_feature._translations_cache.clear()


def resolve_geo_feature(*, mapbox_id, defaults=None):
    """Return one GeoFeature for mapbox_id, merging duplicate rows if present."""
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
    if not fields:
        return
    GeoFeature.objects.filter(pk=geo_feature.pk).update(**fields)
    for field, value in fields.items():
        setattr(geo_feature, field, value)
    _clear_geo_feature_translation_cache(geo_feature)


def collect_geo_features(geolocation):
    if not geolocation.mapbox_id:
        return 0

    current_place_type = geolocation.mapbox_id.split('.')[0]
    languages = list(dict.fromkeys(Language.objects.values_list('code', flat=True)))
    formatter = AddressFormatter() if AddressFormatter else None

    def get_ctx_name(ctx, language):
        translated = (ctx.get('translations') or {}).get(language) or {}
        return translated.get('name') or ctx.get('name')

    def format_place_name(place_type, feature, props, language):
        if not formatter:
            return None

        context = props.get('context') or feature.get('context') or {}
        country_ctx = context.get('country') or {}
        country_code = (
            country_ctx.get('country_code')
            or country_ctx.get('short_code')
            or props.get('short_code')
        )
        country_name = get_ctx_name(country_ctx, language) if country_ctx else None
        street_name = get_ctx_name(context.get('street') or {}, language) if context.get('street') else None
        neighbourhood_name = get_ctx_name(context.get('neighborhood') or {}, language) if context.get(
            'neighborhood') else None
        district_name = get_ctx_name(context.get('district') or {}, language) if context.get('district') else None
        region_name = get_ctx_name(context.get('region') or {}, language) if context.get('region') else None
        place_name = get_ctx_name(context.get('place') or {}, language) if context.get('place') else None
        postcode_name = get_ctx_name(context.get('postcode') or {}, language) if context.get('postcode') else None

        translated = (feature.get('translations') or {}).get(language) or {}
        name = translated.get('name') or feature.get('text') or props.get('name')

        address = {}
        if place_type in ('address', 'secondary_address'):
            address = {
                'house_number': (props.get('address_number') or feature.get('address') or props.get('address')),
                'road': (street_name or feature.get('text') or props.get('name')),
                'city': place_name,
                'postcode': postcode_name,
                'state': region_name,
                'country': country_name,
            }
        elif place_type in ('neighborhood',):
            address = {
                'road': neighbourhood_name,
                'city': place_name,
                'state': region_name,
                'country': country_name,
            }
        elif place_type in ('district',):
            address = {
                'road': district_name,
                'city': place_name,
                'state': region_name,
                'country': country_name,
            }
        elif place_type in ('locality',):
            address = {
                'road': name,
                'city': place_name,
                'state': region_name,
                'country': country_name,
            }
        elif place_type in ('street',):
            address = {
                'road': name,
                'city': place_name,
                'region': region_name,
                'country': country_name,
            }
        elif place_type in ('place',):
            address = {
                'city': name,
                'state': region_name,
                'region': region_name,
                'country': country_name,
            }
        elif place_type == 'region':
            address = {
                'state': name,
                'country': country_name,
            }
        elif place_type == 'country':
            address = {
                'country': name,
            }
        elif place_type == 'postcode':
            address = {
                'postcode': name,
                'city': place_name,
                'state': region_name,
                'country': country_name,
            }

        address = {k: v for k, v in address.items() if v}
        if not address:
            return None

        try:
            formatted = formatter.one_line(address, country=country_code)
        except Exception:
            return None

        return formatted.strip() or None

    def upsert_feature(feature, force_place_type=None, force_update=False):
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
                formatted_place_name = format_place_name(place_type, feature, props, language)
                place_name_value = (
                    formatted_place_name
                    or props.get('full_address')
                    or feature.get('place_name')
                    or props.get('place_formatted')
                    or text_value
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
    context = (selected.get('properties') or {}).get('context') or {}
    created_or_linked = 0

    for place_type in context.keys():
        ctx = context.get(place_type)
        if not ctx:
            continue

        ctx_feature = {
            'id': ctx.get('mapbox_id'),
            'place_type': [place_type],
            'text': ctx.get('name'),
            'place_name': ctx.get('name'),
            'translations': ctx.get('translations') or {},
            'context': context,
            'properties': {
                'short_code': ctx.get('short_code') or ctx.get('country_code'),
                'feature_type': place_type,
                'context': context,
            },
        }
        geo_feature, _created = upsert_feature(
            ctx_feature, force_place_type=place_type, force_update=True,
        )
        if not geo_feature:
            continue
        geolocation.features.add(geo_feature)
        created_or_linked += 1

    sync_geolocation_country(geolocation, context=context, mapbox_feature=selected)

    return created_or_linked
