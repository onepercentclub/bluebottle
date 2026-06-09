"""
Bulk geolocation maintenance — used by scripts/get_geofeatures.py only.
"""
from collections import defaultdict
from contextlib import contextmanager

from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import Q

from bluebottle.geo.legacy_mapbox import BROAD_FORWARD_TYPES, extract_house_number_from_address_fields
from bluebottle.geo.mapbox import (
    coords_from_feature,
    feature_type_from_feature,
    forward_geocode,
    haversine_km,
    mapbox_id_from_feature,
    resolve_mapbox_id_coords,
    reverse_geocode_position,
)
from bluebottle.geo.models import Geolocation


@contextmanager
def pause_elasticsearch_signals():
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


def position_is_null_island(position):
    if not position:
        return False
    try:
        return float(position.x) == 0.0 and float(position.y) == 0.0
    except (TypeError, ValueError, AttributeError):
        return False


def clear_null_island_positions():
    return Geolocation.objects.filter(position=Point(0, 0)).update(position=None)


def backfill_street_number_for_legacy_address_mapbox_ids():
    qs = Geolocation.objects.filter(mapbox_id__startswith='address.').filter(
        Q(street_number__isnull=True) | Q(street_number=''),
    )

    batch = []
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
        if len(batch) >= 500:
            Geolocation.objects.bulk_update(batch, ['street_number'])
            batch = []

    if batch:
        Geolocation.objects.bulk_update(batch, ['street_number'])
    return updated


def try_resolve_mismatch_via_formatted_address(geolocation, *, max_dist_km):
    addr = (geolocation.formatted_address or '').strip()
    if not addr or not geolocation.position:
        return None

    pos_lon = float(geolocation.position.x)
    pos_lat = float(geolocation.position.y)

    feature = forward_geocode(q=addr, proximity_lon=pos_lon, proximity_lat=pos_lat)
    candidates = [feature] if feature else []
    feature_type = feature_type_from_feature(feature) if feature else None
    if feature_type in ('address', 'street') or not feature:
        broader = forward_geocode(
            q=addr,
            proximity_lon=pos_lon,
            proximity_lat=pos_lat,
            types=BROAD_FORWARD_TYPES,
        )
        if broader:
            candidates.append(broader)

    for candidate in candidates:
        coords = coords_from_feature(candidate)
        if not coords:
            continue
        dist = haversine_km(lon1=pos_lon, lat1=pos_lat, lon2=coords[0], lat2=coords[1])
        if dist <= max_dist_km:
            return mapbox_id_from_feature(candidate)

    return None


def resolve_mapbox_mismatch(geolocation, *, max_dist_km, coords_cache):
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

    pos_lon = float(geolocation.position.x)
    pos_lat = float(geolocation.position.y)
    dist_km = haversine_km(
        lon1=pos_lon,
        lat1=pos_lat,
        lon2=resolved[0],
        lat2=resolved[1],
    )
    if dist_km < max_dist_km:
        return None

    new_id = try_resolve_mismatch_via_formatted_address(geolocation, max_dist_km=max_dist_km)
    if new_id:
        return 'via_formatted_address', new_id, dist_km

    fresh = reverse_geocode_position(geolocation.position)
    new_id = mapbox_id_from_feature(fresh) if isinstance(fresh, dict) else None
    if new_id:
        return 'via_reverse', new_id, dist_km

    return None


def delete_unreferenced_geolocations():
    referenced = set()
    for rel in Geolocation._meta.related_objects:
        if not rel.one_to_many:
            continue
        fk_name = rel.field.name
        qs = rel.related_model.objects.exclude(**{f'{fk_name}__isnull': True}).values_list(
            fk_name, flat=True,
        )
        for pk in qs.iterator(chunk_size=5000):
            if pk is not None:
                referenced.add(pk)

    orphan_qs = (
        Geolocation.objects.exclude(pk__in=referenced)
        if referenced else Geolocation.objects.all()
    )

    deleted = 0
    with pause_elasticsearch_signals():
        while True:
            batch = list(orphan_qs.order_by('pk').values_list('pk', flat=True)[:500])
            if not batch:
                break
            deleted += len(batch)
            Geolocation.objects.filter(pk__in=batch).delete()
    return deleted


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
        mapbox_id = (row.get('mapbox_id') or '').strip()
        if not mapbox_id:
            continue
        if mapbox_id.startswith('address.'):
            street_number = row.get('street_number')
            street_number_key = '' if street_number is None else str(street_number).strip()
            key = ('address', mapbox_id, street_number_key)
        else:
            key = ('other', mapbox_id)
        groups[key].append(row['pk'])

    merged_sources = 0
    deleted = set()
    with pause_elasticsearch_signals():
        for pks in groups.values():
            pks = sorted({pk for pk in pks if pk not in deleted})
            if len(pks) < 2:
                continue

            try:
                target = Geolocation.objects.get(pk=pks[0])
            except Geolocation.DoesNotExist:
                deleted.add(pks[0])
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
