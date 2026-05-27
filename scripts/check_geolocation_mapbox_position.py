from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

from django.conf import settings

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.mapbox import (
    coords_from_feature,
    geocode_by_id,
    haversine_km,
    v6_forward_first_feature,
)
from bluebottle.geo.models import Geolocation, PLACE_TYPE_ORDER

_COARSE_PLACE_TYPES = frozenset({"country", "region"})
# Lower rank = finer (more specific) place type; matches GeoFeatureQueryset.order_by_type().
_PLACE_TYPE_RANK = {
    place_type: rank for rank, place_type in enumerate(PLACE_TYPE_ORDER[::-1])
}


def _finest_place_type(geo: Geolocation) -> Optional[str]:
    features = list(geo.features.all())
    if features:
        finest = min(
            features,
            key=lambda feature: _PLACE_TYPE_RANK.get(
                feature.place_type, len(_PLACE_TYPE_RANK)
            ),
        )
        return finest.place_type
    mapbox_id = (geo.mapbox_id or "").strip()
    if "." in mapbox_id:
        return mapbox_id.split(".", 1)[0]
    return None


def _threshold_for_place_type(
    base_threshold_meters: float, finest_place_type: Optional[str]
) -> float:
    if finest_place_type in _COARSE_PLACE_TYPES:
        return base_threshold_meters * 20
    return base_threshold_meters


def _resolve_mapbox_id_coords_cached(
    mapbox_id: str,
    cache: Dict[str, Optional[Tuple[float, float, str]]],
) -> Optional[Tuple[float, float, str]]:
    if mapbox_id in cache:
        return cache[mapbox_id]

    try:
        feature = geocode_by_id(mapbox_id)
        coords = coords_from_feature(feature)
        if isinstance(feature, dict) and coords:
            cache[mapbox_id] = (coords[0], coords[1], str(feature.get('place_name') or ''))
            return cache[mapbox_id]

        feature = v6_forward_first_feature(q=mapbox_id)
        coords = coords_from_feature(feature)
        if isinstance(feature, dict) and coords:
            props = feature.get('properties') or {}
            place_name = str(props.get('full_address') or props.get('name') or '')
            cache[mapbox_id] = (coords[0], coords[1], place_name)
            return cache[mapbox_id]

        cache[mapbox_id] = None
    except Exception:
        cache[mapbox_id] = None

    return cache[mapbox_id]


def find_geolocation_mapbox_position_mismatches(
    *,
    threshold_meters: float = 2000.0,
    limit: Optional[int] = None,
    progress_every: int = 100,
    print_missing_coords: bool = True,
) -> Dict[str, int]:
    """
    Compare Geolocation.position with coordinates returned by geocoding mapbox_id.

    Uses a 20x higher distance threshold when the finest geo feature is country or region.

    Returns counts for summary printing.
    """
    cache: Dict[str, Optional[Tuple[float, float, str]]] = {}

    qs = (
        Geolocation.objects.exclude(mapbox_id__isnull=True)
        .exclude(mapbox_id="")
        .exclude(position__isnull=True)
        .prefetch_related("features")
        .order_by("pk")
    )

    total = None
    if limit is not None:
        total = int(limit)
    else:
        # For typical tenant sizes (~2k) this is fine and makes progress clearer.
        total = qs.count()
    if limit is not None:
        qs = qs[: int(limit)]

    scanned = 0
    missing_coords = 0
    mismatches = 0
    errors = 0
    started = time.monotonic()

    for geo in qs.iterator(chunk_size=500):
        scanned += 1

        mapbox_id = (geo.mapbox_id or '').strip()
        if not mapbox_id or not geo.position:
            continue

        try:
            resolved = _resolve_mapbox_id_coords_cached(mapbox_id, cache)
        except Exception:
            errors += 1
            resolved = None
        if not resolved:
            missing_coords += 1
            if print_missing_coords:
                pos_lon = float(geo.position.x)
                pos_lat = float(geo.position.y)
                print(
                    "pk={pk} mapbox_id={mapbox_id} missing_mapbox_coords "
                    "pos=({pos_lat:.6f},{pos_lon:.6f})".format(
                        pk=geo.pk,
                        mapbox_id=mapbox_id,
                        pos_lat=pos_lat,
                        pos_lon=pos_lon,
                    )
                )
            continue

        mb_lon, mb_lat, mb_place_name = resolved
        pos_lon = float(geo.position.x)
        pos_lat = float(geo.position.y)

        dist_m = haversine_km(
            lon1=pos_lon,
            lat1=pos_lat,
            lon2=mb_lon,
            lat2=mb_lat,
        ) * 1000
        finest_place_type = _finest_place_type(geo)
        effective_threshold_m = _threshold_for_place_type(
            threshold_meters, finest_place_type
        )
        if dist_m >= effective_threshold_m:
            mismatches += 1
            dist_km = dist_m / 1000.0
            print(
                "pk={pk} mapbox_id={mapbox_id} dist_km={dist:.3f} "
                "threshold_m={threshold_m:.0f} finest_place_type={finest_place_type!r} "
                "pos=({pos_lat:.6f},{pos_lon:.6f}) mapbox=({mb_lat:.6f},{mb_lon:.6f}) "
                "place_name={place_name!r}".format(
                    pk=geo.pk,
                    mapbox_id=mapbox_id,
                    dist=dist_km,
                    threshold_m=effective_threshold_m,
                    finest_place_type=finest_place_type,
                    pos_lat=pos_lat,
                    pos_lon=pos_lon,
                    mb_lat=mb_lat,
                    mb_lon=mb_lon,
                    place_name=mb_place_name,
                )
            )

        if progress_every > 0 and scanned % progress_every == 0:
            elapsed = time.monotonic() - started
            rate = (scanned / elapsed) if elapsed > 0 else 0.0
            pct = (scanned / total * 100.0) if total else 0.0
            print(
                "++\nprogress: {scanned}/{total} ({pct:.1f}%) "
                "mismatches={mismatches} missing_coords={missing_coords} errors={errors} "
                "cache={cache} rate={rate:.1f}/s \n------\n".format(
                    scanned=scanned,
                    total=total or "?",
                    pct=pct,
                    mismatches=mismatches,
                    missing_coords=missing_coords,
                    errors=errors,
                    cache=len(cache),
                    rate=rate,
                )
            )

    return {
        "scanned": scanned,
        "mismatches": mismatches,
        "missing_coords": missing_coords,
        "errors": errors,
        "unique_mapbox_ids": len(cache),
    }


def run(*args):
    if not settings.MAPBOX_API_KEY:
        raise RuntimeError("settings.MAPBOX_API_KEY is not set")

    schema_name = None
    threshold_meters: float = 50000.0
    limit: Optional[int] = None
    progress_every: int = 100
    print_missing_coords: bool = True

    for arg in args:
        if arg.startswith("tenant="):
            schema_name = arg.split("=", 1)[1].strip() or None
        elif arg.startswith("threshold_m="):
            threshold_meters = float(arg.split("=", 1)[1])
        elif arg.startswith("limit="):
            limit = int(arg.split("=", 1)[1])
        elif arg.startswith("progress_every="):
            progress_every = int(arg.split("=", 1)[1])
        elif arg.startswith("print_missing="):
            raw = arg.split("=", 1)[1].strip().lower()
            print_missing_coords = raw in ("1", "true", "yes", "y", "on")

    tenants = Client.objects.all()
    if schema_name:
        tenants = tenants.filter(schema_name=schema_name)

    for tenant in tenants:
        with LocalTenant(tenant):
            print(
                f"\n######\n{tenant.schema_name}: checking Geolocation.position vs mapbox_id "
                f"(threshold_m={threshold_meters}, limit={limit})…"
            )
            stats = find_geolocation_mapbox_position_mismatches(
                threshold_meters=threshold_meters,
                limit=limit,
                progress_every=progress_every,
                print_missing_coords=print_missing_coords,
            )
            print(f"{tenant.schema_name}: done: {stats}")
