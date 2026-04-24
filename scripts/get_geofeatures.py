import math
from collections import defaultdict
from typing import Optional, Tuple

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation
from bluebottle.geo.utils import extract_house_number_from_address_fields


def _haversine_km(*, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0088  # km
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _coords_from_mapbox_feature_dict(feature) -> Optional[Tuple[float, float]]:
    if not isinstance(feature, dict):
        return None
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates")
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        try:
            return float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            return None
    center = feature.get("center")
    if isinstance(center, (list, tuple)) and len(center) >= 2:
        try:
            return float(center[0]), float(center[1])
        except (TypeError, ValueError):
            return None
    return None


def _resolve_mapbox_id_coords(geolocation: Geolocation) -> Optional[Tuple[float, float]]:
    """
    Resolve coordinates for a stored mapbox id.

    Legacy ids like `poi.*` are reliably resolved via the v5 Places API
    (`Geolocation.geocode_by_id`), while modern ids often work via v6 forward in
    `collect_geo_features`. Try v5 first, then fall back to v6 forward.
    """
    feature = geolocation.geocode_by_id(geolocation.mapbox_id)
    coords = _coords_from_mapbox_feature_dict(feature)
    if coords:
        return coords

    # v6 forward fallback (helps some legacy ids that v5 doesn't resolve)
    try:
        import requests

        response = requests.get(
            "https://api.mapbox.com/search/geocode/v6/forward",
            params={
                "q": geolocation.mapbox_id,
                "access_token": settings.MAPBOX_API_KEY,
                "permanent": "true",
                "limit": 1,
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json() or {}
        features = data.get("features") or []
        if not features:
            return None
        return _coords_from_mapbox_feature_dict(features[0])
    except Exception:
        return None


def _v6_forward_first_feature(
    *,
    q: str,
    proximity_lon: Optional[float] = None,
    proximity_lat: Optional[float] = None,
    types: Optional[str] = None,
) -> Optional[dict]:
    if not (q or "").strip():
        return None
    import requests

    params = {
        "q": q.strip(),
        "access_token": settings.MAPBOX_API_KEY,
        "permanent": "true",
        "limit": 1,
    }
    if proximity_lon is not None and proximity_lat is not None:
        params["proximity"] = f"{proximity_lon},{proximity_lat}"
    if types:
        params["types"] = types
    response = requests.get(
        "https://api.mapbox.com/search/geocode/v6/forward",
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json() or {}
    features = data.get("features") or []
    return features[0] if features else None


def _mapbox_id_from_v6_feature(feature: dict) -> Optional[str]:
    if not isinstance(feature, dict):
        return None
    props = feature.get("properties") or {}
    return feature.get("id") or props.get("mapbox_id")


def _feature_type_from_v6(feature: dict) -> Optional[str]:
    if not isinstance(feature, dict):
        return None
    props = feature.get("properties") or {}
    return props.get("feature_type") or ((feature.get("place_type") or [None])[0])


def _try_resolve_mismatch_via_formatted_address(
    location: Geolocation,
    *,
    max_dist_km: float,
) -> Optional[str]:
    """
    When stored mapbox_id disagrees with position, prefer re-resolving from the
    human-readable formatted_address (biased by position) so we get an appropriate
    granularity (e.g. city) rather than jumping straight to a pin reverse result.
    """
    addr = (location.formatted_address or "").strip()
    if not addr or not location.position:
        return None

    pos_lon = float(location.position.x)
    pos_lat = float(location.position.y)

    feature = _v6_forward_first_feature(
        q=addr,
        proximity_lon=pos_lon,
        proximity_lat=pos_lat,
    )
    coords = _coords_from_mapbox_feature_dict(feature) if feature else None
    if coords:
        dist = _haversine_km(
            lon1=pos_lon,
            lat1=pos_lat,
            lon2=coords[0],
            lat2=coords[1],
        )
        if dist <= max_dist_km:
            return _mapbox_id_from_v6_feature(feature)

    # If the open query snapped to street/address far from the pin, try place-focused types.
    ftype = _feature_type_from_v6(feature) if feature else None
    if ftype in ("address", "street") or not feature:
        feature2 = _v6_forward_first_feature(
            q=addr,
            proximity_lon=pos_lon,
            proximity_lat=pos_lat,
            types="place,locality,district,region,postcode,country",
        )
        coords2 = _coords_from_mapbox_feature_dict(feature2) if feature2 else None
        if coords2:
            dist2 = _haversine_km(
                lon1=pos_lon,
                lat1=pos_lat,
                lon2=coords2[0],
                lat2=coords2[1],
            )
            if dist2 <= max_dist_km:
                return _mapbox_id_from_v6_feature(feature2)

    return None


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

    if referenced:
        orphan_qs = Geolocation.objects.exclude(pk__in=referenced)
    else:
        orphan_qs = Geolocation.objects.all()

    batch_size = 500
    deleted = 0
    while True:
        batch = list(
            orphan_qs.order_by('pk').values_list('pk', flat=True)[:batch_size],
        )
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
    with transaction.atomic():
        for feature in source.features.all():
            target.features.add(feature)
        for rel in Geolocation._meta.related_objects:
            if rel.one_to_many:
                rel.related_model.objects.filter(**{
                    rel.field.name: source,
                }).update(**{
                    rel.field.name: target,
                })
        source.delete()


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
    for _key, pks in groups.items():
        if len(pks) < 2:
            continue
        pks.sort()
        target_pk = pks[0]
        target = Geolocation.objects.get(pk=target_pk)
        for source_pk in pks[1:]:
            source = Geolocation.objects.get(pk=source_pk)
            merge_geolocations_fk_only(source, target)
            merged_sources += 1
    return merged_sources


def run(*args):
    if not settings.MAPBOX_API_KEY:
        raise RuntimeError('settings.MAPBOX_API_KEY is not set')

    schema_name = None
    mapbox_mismatch_km = 10.0
    for arg in args:
        if arg.startswith("tenant="):
            schema_name = arg.split("=", 1)[1].strip() or None
        elif arg.startswith("mismatch_km="):
            mapbox_mismatch_km = float(arg.split("=", 1)[1])

    tenants = Client.objects.all()
    if schema_name:
        tenants = tenants.filter(schema_name=schema_name)

    for tenant in tenants:
        with LocalTenant(tenant):
            print(f'{tenant.schema_name}: backfill street_number (address.*)…')
            n_backfill = backfill_street_number_for_legacy_address_mapbox_ids()
            print(f'{tenant.schema_name}: updated street_number on {n_backfill} rows')

            print(f'{tenant.schema_name}: delete geolocations with no reverse FK…')
            n_deleted = delete_unreferenced_geolocations()
            print(f'{tenant.schema_name}: deleted {n_deleted} unreferenced rows')

            print(f'{tenant.schema_name}: merge duplicate geolocations…')
            n_merged = merge_duplicate_geolocations()
            print(f'{tenant.schema_name}: merged {n_merged} duplicate source rows')

            qs = Geolocation.objects.exclude(mapbox_id__startswith='dXJ').all().order_by('pk')
            total = qs.count()
            print(
                f'{tenant.schema_name}: save {total} geolocations (normalize + collect_geo_features)… '
                f'(mismatch_km={mapbox_mismatch_km})'
            )

            # Cache v6-resolved coordinates per mapbox_id to reduce API calls.
            resolved_coords_cache = {}

            for n, location in enumerate(qs.iterator(), start=1):
                # If the stored mapbox_id resolves far away from the known position, prefer a fresh
                # reverse-geocode from the position to re-collect higher-quality geo features.
                if (
                    location.position
                    and location.mapbox_id
                    and location.mapbox_id not in resolved_coords_cache
                ):
                    try:
                        resolved_coords_cache[location.mapbox_id] = _resolve_mapbox_id_coords(location)
                    except Exception:
                        resolved_coords_cache[location.mapbox_id] = None

                if location.position and location.mapbox_id:
                    resolved = resolved_coords_cache.get(location.mapbox_id)
                    if resolved:
                        mb_lon, mb_lat = resolved
                        pos_lon = float(location.position.x)
                        pos_lat = float(location.position.y)
                        dist_km = _haversine_km(
                            lon1=pos_lon,
                            lat1=pos_lat,
                            lon2=mb_lon,
                            lat2=mb_lat,
                        )
                        if dist_km >= mapbox_mismatch_km:
                            try:
                                new_id = _try_resolve_mismatch_via_formatted_address(
                                    location,
                                    max_dist_km=mapbox_mismatch_km,
                                )
                                if new_id:
                                    old = location.mapbox_id
                                    location.mapbox_id = new_id
                                    location.save()
                                    print(
                                        f"{tenant.schema_name}: pk={location.pk} mapbox mismatch "
                                        f"{dist_km:.3f}km via_formatted_address old={old!r} new={location.mapbox_id!r}"
                                    )
                                    continue

                                fresh = location.reverse_geocode()
                                if isinstance(fresh, dict) and fresh.get("id"):
                                    old = location.mapbox_id
                                    location.mapbox_id = fresh["id"]
                                    # Saving will normalize mapbox_id and re-collect features.
                                    location.save()
                                    print(
                                        f"{tenant.schema_name}: pk={location.pk} mapbox mismatch "
                                        f"{dist_km:.3f}km via_reverse old={old!r} new={location.mapbox_id!r}"
                                    )
                                    continue
                            except Exception:
                                pass

                location.save()
                if n % 100 == 0 or n == total:
                    print(f'{tenant.schema_name}: save {n}/{total}')
            n_merged = merge_duplicate_geolocations()
            print(f'{tenant.schema_name}: merged another {n_merged} duplicate source rows')
            print(f'{tenant.schema_name}: done')
