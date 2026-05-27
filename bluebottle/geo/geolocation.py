"""
Geolocation business logic: id normalization, country sync, maintenance operations.

Model field definitions live in geo.models.Geolocation; Mapbox HTTP calls in geo.mapbox.
GeoFeature collection lives in geo.geofeatures.
"""
from __future__ import annotations

import re
from collections import defaultdict
from contextlib import contextmanager
from typing import Optional, Tuple

import requests
from django.conf import settings
from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Q

from bluebottle.geo.mapbox import (
    coords_from_feature,
    feature_type_from_feature,
    haversine_km,
    is_modern_mapbox_id,
    mapbox_id_from_feature,
    resolve_mapbox_id_coords,
    reverse_geocode_position,
    v6_forward_first_feature,
)
from bluebottle.geo.models import Country, Geolocation

# ---------------------------------------------------------------------------
# Address parsing
# ---------------------------------------------------------------------------


def extract_house_number_from_address_fields(
    street_number: Optional[str] = None,
    street: Optional[str] = None,
    formatted_address: Optional[str] = None,
) -> Optional[str]:
    if street_number:
        candidate = str(street_number).strip()
        if re.match(r'^\d+[A-Za-z]?$', candidate):
            return candidate
    if street:
        match = re.search(r'\b(\d+[A-Za-z]?)\b', str(street).strip())
        if match:
            return match.group(1)
    if formatted_address:
        first_line = str(formatted_address).split(',')[0].strip()
        if first_line:
            matches = list(re.finditer(r'\b(\d+[A-Za-z]?)\b', first_line))
            if matches:
                return matches[-1].group(1)
    return None


# ---------------------------------------------------------------------------
# Country resolution
# ---------------------------------------------------------------------------


def _normalize_country_alpha2(code):
    if not code:
        return None
    code = str(code).strip()
    if '-' in code:
        code = code.split('-', 1)[0]
    if len(code) != 2:
        return None
    return code.upper()


def resolve_country_from_code(code):
    alpha2 = _normalize_country_alpha2(code)
    if not alpha2:
        return None
    return Country.objects.filter(alpha2_code__iexact=alpha2).first()


def resolve_country_from_mapbox_context(context):
    if not context:
        return None

    if isinstance(context, dict):
        country_ctx = context.get('country') or {}
        return resolve_country_from_code(
            country_ctx.get('country_code') or country_ctx.get('short_code'),
        )

    if isinstance(context, list):
        for item in context:
            item_id = item.get('id') or ''
            if item_id.startswith('country.'):
                return resolve_country_from_code(item.get('short_code'))

    return None


def resolve_country_from_mapbox_feature(feature):
    if not feature:
        return None

    props = feature.get('properties') or {}
    place_types = feature.get('place_type') or []
    if place_types and place_types[0] == 'country':
        country = resolve_country_from_code(
            props.get('country_code') or props.get('short_code'),
        )
        if country:
            return country

    country = resolve_country_from_mapbox_context(props.get('context'))
    if country:
        return country

    return resolve_country_from_mapbox_context(feature.get('context'))


def sync_geolocation_country(geolocation, *, context=None, mapbox_feature=None):
    """Set geolocation.country from Mapbox context/feature or linked country GeoFeature."""
    country = None
    if mapbox_feature:
        country = resolve_country_from_mapbox_feature(mapbox_feature)
    if not country and context is not None:
        country = resolve_country_from_mapbox_context(context)
    if not country:
        country_feature = geolocation.features.filter(place_type='country').first()
        if country_feature and country_feature.code:
            country = resolve_country_from_code(country_feature.code)

    if country and geolocation.country_id != country.pk:
        geolocation.country = country
        if geolocation.pk:
            Geolocation.objects.filter(pk=geolocation.pk).update(country_id=country.pk)

    return country


# ---------------------------------------------------------------------------
# Mapbox id normalization
# ---------------------------------------------------------------------------


def normalize_mapbox_id(
    *,
    mapbox_id: Optional[str],
    street: Optional[str] = None,
    street_number: Optional[str] = None,
    formatted_address: Optional[str] = None,
    locality: Optional[str] = None,
    province: Optional[str] = None,
    country_name: Optional[str] = None,
    position: Optional[Tuple[float, float]] = None,
    access_token: Optional[str] = None,
) -> Optional[str]:
    """
    Normalize legacy v5-style ids (``place.123``, ``address.456``) to modern v6 ids.
    Returns the new id, or the original when it cannot be resolved.
    """
    if not mapbox_id:
        return None

    token = access_token or settings.MAPBOX_API_KEY
    if not token:
        return mapbox_id

    current = str(mapbox_id).strip()

    def v6_forward(params):
        response = requests.get(
            'https://api.mapbox.com/search/geocode/v6/forward',
            params={**params, 'access_token': token, 'limit': 1},
            timeout=30,
        )
        response.raise_for_status()
        features = (response.json() or {}).get('features') or []
        return features[0] if features else None

    if '.' in current and not is_modern_mapbox_id(current):
        resolved = v6_forward({'q': current, 'permanent': 'true'})
        resolved_id = mapbox_id_from_feature(resolved) if resolved else None
        if resolved_id and is_modern_mapbox_id(resolved_id):
            current = resolved_id

    if mapbox_id.startswith('address.') and not is_modern_mapbox_id(current):
        house_number = extract_house_number_from_address_fields(
            street_number=street_number,
            street=street,
            formatted_address=formatted_address,
        )
        query_parts = []
        street_line = str(street).strip() if street else ''
        if not street_line and formatted_address:
            street_line = str(formatted_address).split(',')[0].strip()
        if street_line:
            if house_number and house_number not in street_line:
                query_parts.append(f'{street_line} {house_number}')
            else:
                query_parts.append(street_line)
        if locality:
            query_parts.append(str(locality))
        if country_name:
            query_parts.append(str(country_name))
        elif province:
            query_parts.append(str(province))

        q = ', '.join(part for part in query_parts if part)
        if q:
            params = {'q': q, 'types': 'address', 'permanent': 'true'}
            if position:
                params['proximity'] = f'{position[0]},{position[1]}'
            resolved = v6_forward(params)
            if not resolved:
                params['types'] = 'address,street,place,locality,postcode,district,region,country'
                resolved = v6_forward(params)

            resolved_id = mapbox_id_from_feature(resolved) if resolved else None
            resolved_type = feature_type_from_feature(resolved) if resolved else None

            if not house_number and resolved_type in ('street', 'address'):
                context = ((resolved or {}).get('properties') or {}).get('context') or {}
                for preferred in ('place', 'locality', 'district', 'region', 'country', 'postcode'):
                    ctx = context.get(preferred) or {}
                    ctx_id = ctx.get('mapbox_id')
                    if ctx_id and is_modern_mapbox_id(str(ctx_id)):
                        current = str(ctx_id)
                        break
                else:
                    if resolved_id and is_modern_mapbox_id(resolved_id):
                        current = resolved_id
            elif resolved_id and is_modern_mapbox_id(resolved_id):
                current = resolved_id

    return current


# ---------------------------------------------------------------------------
# Save-time sync (called from Geolocation.save)
# ---------------------------------------------------------------------------


def prepare_geolocation_for_save(geolocation) -> Optional[str]:
    """Normalize mapbox_id before persisting. Returns previous mapbox_id when updating."""
    old_mapbox_id = None
    if geolocation.pk:
        old_mapbox_id = (
            Geolocation.objects.filter(pk=geolocation.pk)
            .values_list('mapbox_id', flat=True)
            .first()
        )

    if settings.MAPBOX_API_KEY and geolocation.mapbox_id:
        geolocation.mapbox_id = normalize_mapbox_id(
            mapbox_id=geolocation.mapbox_id,
            street=geolocation.street,
            street_number=geolocation.street_number,
            formatted_address=geolocation.formatted_address,
            locality=geolocation.locality,
            province=geolocation.province,
            country_name=geolocation.country.name if geolocation.country_id else None,
            position=(geolocation.position.x, geolocation.position.y) if geolocation.position else None,
        )

    return old_mapbox_id


def sync_geolocation_after_save(geolocation, *, creating: bool, old_mapbox_id=None):
    """Collect GeoFeatures and country after the row has been saved."""
    if not (settings.MAPBOX_API_KEY and geolocation.mapbox_id):
        return

    from bluebottle.geo.geofeatures import collect_geo_features

    if creating or old_mapbox_id != geolocation.mapbox_id or not geolocation.features.exists():
        geolocation.features.clear()
        collect_geo_features(geolocation)
    elif not geolocation.country_id:
        sync_geolocation_country(geolocation)


# ---------------------------------------------------------------------------
# Mapbox id / position mismatch resolution (maintenance scripts)
# ---------------------------------------------------------------------------


def position_is_null_island(position) -> bool:
    if not position:
        return False
    try:
        return float(position.x) == 0.0 and float(position.y) == 0.0
    except (TypeError, ValueError, AttributeError):
        return False


def try_resolve_mismatch_via_formatted_address(
    geolocation: Geolocation,
    *,
    max_dist_km: float,
) -> Optional[str]:
    """
    Re-resolve mapbox_id from formatted_address when it disagrees with position.
    """
    addr = (geolocation.formatted_address or '').strip()
    if not addr or not geolocation.position:
        return None

    pos_lon = float(geolocation.position.x)
    pos_lat = float(geolocation.position.y)

    feature = v6_forward_first_feature(
        q=addr,
        proximity_lon=pos_lon,
        proximity_lat=pos_lat,
    )
    coords = coords_from_feature(feature) if feature else None
    if coords:
        dist = haversine_km(lon1=pos_lon, lat1=pos_lat, lon2=coords[0], lat2=coords[1])
        if dist <= max_dist_km:
            return mapbox_id_from_feature(feature)

    ftype = feature_type_from_feature(feature) if feature else None
    if ftype in ('address', 'street') or not feature:
        feature2 = v6_forward_first_feature(
            q=addr,
            proximity_lon=pos_lon,
            proximity_lat=pos_lat,
            types='place,locality,district,region,postcode,country',
        )
        coords2 = coords_from_feature(feature2) if feature2 else None
        if coords2:
            dist2 = haversine_km(lon1=pos_lon, lat1=pos_lat, lon2=coords2[0], lat2=coords2[1])
            if dist2 <= max_dist_km:
                return mapbox_id_from_feature(feature2)

    return None


def resolve_mapbox_mismatch(
    geolocation: Geolocation,
    *,
    max_dist_km: float,
    coords_cache: dict,
) -> Optional[Tuple[str, str, float]]:
    """
    When mapbox_id coords disagree with position, try formatted-address then reverse geocode.

    Returns (method, new_mapbox_id, distance_km) or None.
    """
    if not (geolocation.position and geolocation.mapbox_id):
        return None

    mapbox_id = geolocation.mapbox_id
    if mapbox_id not in coords_cache:
        try:
            coords_cache[mapbox_id] = resolve_mapbox_id_coords(mapbox_id)
        except Exception:
            coords_cache[mapbox_id] = None

    resolved = coords_cache.get(mapbox_id)
    if not resolved:
        return None

    mb_lon, mb_lat = resolved
    pos_lon = float(geolocation.position.x)
    pos_lat = float(geolocation.position.y)
    dist_km = haversine_km(lon1=pos_lon, lat1=pos_lat, lon2=mb_lon, lat2=mb_lat)
    if dist_km < max_dist_km:
        return None

    new_id = try_resolve_mismatch_via_formatted_address(geolocation, max_dist_km=max_dist_km)
    if new_id:
        return 'via_formatted_address', new_id, dist_km

    fresh = reverse_geocode_position(geolocation.position)
    if isinstance(fresh, dict) and fresh.get('id'):
        return 'via_reverse', fresh['id'], dist_km

    return None


# ---------------------------------------------------------------------------
# Bulk maintenance (used by scripts/get_geofeatures.py)
# ---------------------------------------------------------------------------


@contextmanager
def pause_elasticsearch_signals():
    """
    Bulk geolocation merge/delete queues Celery ES tasks that pickle querysets
    tied to the deleted row; pause signals for the duration of the operation.
    """
    from django.apps import apps

    processor = apps.get_app_config('django_elasticsearch_dsl').signal_processor
    if processor is None:
        yield
        return
    processor.teardown()
    try:
        yield
    finally:
        processor.setup()


def clear_null_island_positions():
    """Unset (0, 0) positions — a common placeholder that causes bad merges."""
    return Geolocation.objects.filter(position=Point(0, 0)).update(position=None)


def backfill_street_number_for_legacy_address_mapbox_ids():
    qs = Geolocation.objects.filter(mapbox_id__startswith='address.').filter(
        Q(street_number__isnull=True) | Q(street_number=''),
    )
    batch = []
    batch_size = 500
    updated = 0
    for obj in qs.iterator():
        num = extract_house_number_from_address_fields(
            street_number=obj.street_number,
            street=obj.street,
            formatted_address=obj.formatted_address,
        )
        if not num:
            continue
        obj.street_number = num
        batch.append(obj)
        updated += 1
        if len(batch) >= batch_size:
            Geolocation.objects.bulk_update(batch, ['street_number'])
            batch = []
    if batch:
        Geolocation.objects.bulk_update(batch, ['street_number'])
    return updated


def delete_unreferenced_geolocations():
    referenced = set()
    for rel in Geolocation._meta.related_objects:
        if not rel.one_to_many:
            continue
        fk_name = rel.field.name
        rel_model = rel.related_model
        qs = rel_model.objects.exclude(**{f'{fk_name}__isnull': True}).values_list(
            fk_name, flat=True,
        )
        for pk in qs.iterator(chunk_size=5000):
            if pk is not None:
                referenced.add(pk)

    orphan_qs = (
        Geolocation.objects.exclude(pk__in=referenced)
        if referenced else Geolocation.objects.all()
    )

    batch_size = 500
    deleted = 0
    with pause_elasticsearch_signals():
        while True:
            batch = list(orphan_qs.order_by('pk').values_list('pk', flat=True)[:batch_size])
            if not batch:
                break
            deleted += len(batch)
            Geolocation.objects.filter(pk__in=batch).delete()
    return deleted


def _cluster_key(row):
    mapbox_id = (row.get('mapbox_id') or '').strip()
    if not mapbox_id:
        return None
    if mapbox_id.startswith('address.'):
        sn = row.get('street_number')
        sn_key = '' if sn is None else str(sn).strip()
        return ('address', mapbox_id, sn_key)
    return ('other', mapbox_id)


def merge_geolocations_fk_only(source, target):
    source_pk = source.pk
    target_pk = target.pk
    with transaction.atomic():
        for feature in source.features.all():
            target.features.add(feature)
        for rel in Geolocation._meta.related_objects:
            if rel.one_to_many:
                rel.related_model.objects.filter(**{
                    rel.field.name: source_pk,
                }).update(**{
                    rel.field.name: target_pk,
                })
        Geolocation.objects.filter(pk=source_pk).delete()


def merge_duplicate_geolocations():
    rows = (
        Geolocation.objects.exclude(
            Q(mapbox_id__isnull=True) | Q(mapbox_id=''),
        )
        .values('pk', 'mapbox_id', 'street_number')
        .order_by('pk')
    )

    groups = defaultdict(list)
    for row in rows.iterator(chunk_size=2000):
        key = _cluster_key(row)
        if key is None:
            continue
        groups[key].append(row['pk'])

    merged_sources = 0
    deleted = set()
    with pause_elasticsearch_signals():
        for _key, pks in groups.items():
            pks = sorted({pk for pk in pks if pk not in deleted})
            if len(pks) < 2:
                continue
            target_pk = pks[0]
            try:
                target = Geolocation.objects.get(pk=target_pk)
            except Geolocation.DoesNotExist:
                deleted.add(target_pk)
                continue
            for source_pk in pks[1:]:
                if source_pk in deleted:
                    continue
                try:
                    source = Geolocation.objects.get(pk=source_pk)
                except Geolocation.DoesNotExist:
                    deleted.add(source_pk)
                    continue
                merge_geolocations_fk_only(source, target)
                deleted.add(source_pk)
                merged_sources += 1
    return merged_sources
