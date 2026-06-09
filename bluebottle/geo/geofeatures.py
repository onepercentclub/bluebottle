from django.conf import settings
from django.db import IntegrityError

from bluebottle.geo.legacy_mapbox import is_legacy_id, upgrade_mapbox_id
from bluebottle.geo.mapbox import forward_geocode, mapbox_id_from_feature
from bluebottle.geo.models import Country, GeoFeature, Geolocation
from bluebottle.utils.models import Language

CONTEXT_PLACE_TYPES = (
    'address',
    'secondary_address',
    'street',
    'postcode',
    'locality',
    'district',
    'neighborhood',
    'country',
)


def _join_unique(*parts):
    values = []
    for part in parts:
        if part and (not values or values[-1] != part):
            values.append(str(part))
    return ', '.join(values) or None


def place_name(place_type, feature, props, language):
    context = props.get('context') or feature.get('context') or {}

    def ctx_name(key):
        entry = context.get(key) or {}
        translations = entry.get('translations') or {}
        return (translations.get(language) or {}).get('name') or entry.get('name')

    names = {key: ctx_name(key) for key in context if context.get(key)}
    translations = feature.get('translations') or {}
    name = (
        (translations.get(language) or {}).get('name')
        or feature.get('text')
        or props.get('name')
        or props.get('place_formatted')
        or props.get('full_address')
    )

    if place_type in ('address', 'secondary_address'):
        house_number = props.get('address_number') or feature.get('address') or props.get('address')
        street = names.get('street') or name
        street_line = (
            f'{street} {house_number}'
            if house_number and str(house_number) not in str(street)
            else street
        )
        return _join_unique(street_line, names.get('postcode'), names.get('place'), names.get('country'))

    if place_type == 'postcode':
        return _join_unique(name, names.get('place'), names.get('country'))

    if place_type in ('street', 'locality', 'district', 'neighborhood'):
        return _join_unique(name, names.get('place'), names.get('country'))

    if place_type == 'place':
        return _join_unique(name, names.get('region'), names.get('country'))

    if place_type == 'region':
        return _join_unique(name, names.get('country'))

    return name or props.get('full_address') or props.get('place_formatted') or feature.get('place_name')


_place_name = place_name


def resolve_geo_feature(*, mapbox_id, defaults=None):
    matches = list(GeoFeature.objects.filter(mapbox_id=mapbox_id).order_by('pk'))
    if not matches:
        return GeoFeature.objects.create(mapbox_id=mapbox_id, **(defaults or {})), True

    canonical = matches[0]
    translations = canonical._parler_meta.root.model

    for duplicate in matches[1:]:
        for geolocation in Geolocation.objects.filter(features=duplicate):
            geolocation.features.remove(duplicate)
            geolocation.features.add(canonical)

        for translation in translations.objects.filter(master_id=duplicate.pk):
            translations.objects.get_or_create(
                master_id=canonical.pk,
                language_code=translation.language_code,
                defaults={
                    'name': translation.name,
                    'place_name': translation.place_name,
                },
            )
        duplicate.delete()

    return canonical, not matches


def _feature_name(feature, props, language):
    translations = feature.get('translations') or {}
    return (
        (translations.get(language) or {}).get('name')
        or feature.get('text')
        or props.get('name')
        or props.get('place_formatted')
        or props.get('full_address')
    )


def _feature_code(props, place_type):
    if place_type == 'country':
        return props.get('country_code')
    return props.get('short_code')


def upsert_geofeature(feature, *, place_type, languages):
    props = feature.get('properties') or {}
    mapbox_id = feature.get('id') or props.get('mapbox_id')
    if not mapbox_id:
        return None

    code = _feature_code(props, place_type)
    geo_feature, _created = resolve_geo_feature(
        mapbox_id=mapbox_id,
        defaults={'code': code, 'place_type': place_type},
    )

    updates = {}
    if geo_feature.place_type != place_type:
        updates['place_type'] = place_type
    if code and geo_feature.code != code:
        updates['code'] = code
    if updates:
        GeoFeature.objects.filter(pk=geo_feature.pk).update(**updates)
        for field, value in updates.items():
            setattr(geo_feature, field, value)

    translation_model = geo_feature._parler_meta.root.model
    for language in languages:
        defaults = {
            'name': _feature_name(feature, props, language),
            'place_name': place_name(place_type, feature, props, language),
        }
        defaults['place_name'] = defaults['place_name'] or defaults['name']
        try:
            translation_model.objects.update_or_create(
                master_id=geo_feature.pk,
                language_code=language,
                defaults=defaults,
            )
        except IntegrityError:
            translation_model.objects.filter(
                master_id=geo_feature.pk,
                language_code=language,
            ).update(**defaults)

    cache = getattr(geo_feature, '_translations_cache', None)
    if cache is not None:
        cache.clear()

    return geo_feature


def _context_feature(place_type, ctx, context):
    properties = {'feature_type': place_type, 'context': context}
    if place_type == 'country':
        properties['country_code'] = ctx.get('country_code')
    elif ctx.get('short_code'):
        properties['short_code'] = ctx.get('short_code')

    return {
        'id': ctx.get('mapbox_id'),
        'place_type': [place_type],
        'text': ctx.get('name'),
        'translations': ctx.get('translations') or {},
        'context': context,
        'properties': properties,
    }


def _sync_country(geolocation):
    country_feature = geolocation.features.filter(place_type='country').first()
    if not country_feature or not country_feature.code:
        return None

    code = str(country_feature.code).strip().upper()[:2]
    country = Country.objects.filter(alpha2_code__iexact=code).first()
    if not country:
        return None

    if geolocation.country_id != country.pk:
        geolocation.country = country
        Geolocation.objects.filter(pk=geolocation.pk).update(country_id=country.pk)

    return country


def sync_geolocation(geolocation):
    """
    Upgrade legacy mapbox ids, fetch v6 context, upsert GeoFeatures, set country.

    Called from Geolocation.save() and migration scripts.
    """
    if not geolocation.mapbox_id or not settings.MAPBOX_API_KEY:
        return 0

    if is_legacy_id(geolocation.mapbox_id):
        upgrade_mapbox_id(geolocation)

    languages = list(dict.fromkeys(Language.objects.values_list('code', flat=True)))
    selected = forward_geocode(
        q=geolocation.mapbox_id,
        languages=','.join(languages),
        permanent=True,
    )
    if not selected:
        return 0

    props = selected.get('properties') or {}
    context = props.get('context') or {}
    primary_id = selected.get('id') or props.get('mapbox_id')
    primary_type = (
        props.get('feature_type')
        or (selected.get('place_type') or [None])[0]
        or geolocation.mapbox_id.split('.')[0]
    )

    selected['context'] = context
    selected['properties'] = props | {'context': context}

    geolocation.features.clear()
    linked = []

    primary = upsert_geofeature(selected, place_type=primary_type, languages=languages)
    if primary:
        geolocation.features.add(primary)
        linked.append(primary)

    for place_type, ctx in context.items():
        if not ctx or place_type not in CONTEXT_PLACE_TYPES:
            continue
        if ctx.get('mapbox_id') == primary_id:
            continue
        geo_feature = upsert_geofeature(
            _context_feature(place_type, ctx, context),
            place_type=place_type,
            languages=languages,
        )
        if geo_feature:
            geolocation.features.add(geo_feature)
            linked.append(geo_feature)

    _sync_country(geolocation)
    return len(linked)


collect_geo_features = sync_geolocation
