from __future__ import annotations

import math
import time
from typing import Any, Dict, Optional, Tuple

import requests
from django.conf import settings

from bluebottle.clients.models import Client
from bluebottle.clients.utils import LocalTenant
from bluebottle.geo.models import Geolocation


def _haversine_meters(
    *,
    lon1: float,
    lat1: float,
    lon2: float,
    lat2: float,
) -> float:
    # Earth radius (WGS84-ish mean), meters
    r = 6371008.8
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


def _coords_from_mapbox_feature(feature: Any) -> Optional[Tuple[float, float]]:
    if not isinstance(feature, dict):
        return None

    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates")
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        try:
            return float(coords[0]), float(coords[1])  # lon, lat
        except (TypeError, ValueError):
            return None

    center = feature.get("center")
    if isinstance(center, (list, tuple)) and len(center) >= 2:
        try:
            return float(center[0]), float(center[1])  # lon, lat
        except (TypeError, ValueError):
            return None

    return None


def find_geolocation_mapbox_position_mismatches(
    *,
    threshold_meters: float = 2000.0,
    limit: Optional[int] = None,
    progress_every: int = 100,
    print_missing_coords: bool = True,
) -> Dict[str, int]:
    """
    Compare Geolocation.position with coordinates returned by geocoding mapbox_id.

    Returns counts for summary printing.
    """
    cache: Dict[str, Optional[Tuple[float, float, str]]] = {}

    qs = (
        Geolocation.objects.exclude(mapbox_id__isnull=True)
        .exclude(mapbox_id="")
        .exclude(position__isnull=True)
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
    token = settings.MAPBOX_API_KEY

    for geo in qs.iterator(chunk_size=500):
        scanned += 1

        mapbox_id = (geo.mapbox_id or "").strip()
        if not mapbox_id or not geo.position:
            continue

        cached = cache.get(mapbox_id)
        if cached is None and mapbox_id not in cache:
            try:
                # Legacy ids like `poi.*` are typically resolved via v5 Places permanent id lookup.
                feature = geo.geocode_by_id(mapbox_id)
                coords = _coords_from_mapbox_feature(feature)
                if isinstance(feature, dict) and coords:
                    place_name = str(feature.get("place_name") or "")
                    cache[mapbox_id] = (coords[0], coords[1], place_name)
                else:
                    params = {"q": mapbox_id, "permanent": "true"}
                    response = requests.get(
                        "https://api.mapbox.com/search/geocode/v6/forward",
                        params={**params, "access_token": token, "limit": 1},
                        timeout=30,
                    )
                    response.raise_for_status()
                    data = response.json() or {}
                    features = data.get("features") or []
                    feature = features[0] if features else {}
                    if isinstance(feature, dict):
                        coords = _coords_from_mapbox_feature(feature)
                        place_name = str(feature.get("place_name") or "")
                        if coords:
                            cache[mapbox_id] = (coords[0], coords[1], place_name)
                        else:
                            cache[mapbox_id] = None
                    else:
                        cache[mapbox_id] = None
            except Exception:
                errors += 1
                cache[mapbox_id] = None

        resolved = cache.get(mapbox_id)
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

        dist_m = _haversine_meters(
            lon1=pos_lon,
            lat1=pos_lat,
            lon2=mb_lon,
            lat2=mb_lat,
        )
        if dist_m >= threshold_meters:
            mismatches += 1
            dist_km = dist_m / 1000.0
            print(
                "pk={pk} mapbox_id={mapbox_id} dist_km={dist:.3f} "
                "pos=({pos_lat:.6f},{pos_lon:.6f}) mapbox=({mb_lat:.6f},{mb_lon:.6f}) "
                "place_name={place_name!r}".format(
                    pk=geo.pk,
                    mapbox_id=mapbox_id,
                    dist=dist_km,
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
                "progress: {scanned}/{total} ({pct:.1f}%) "
                "mismatches={mismatches} missing_coords={missing_coords} errors={errors} "
                "cache={cache} rate={rate:.1f}/s".format(
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
    threshold_meters: float = 2000.0
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
                f"{tenant.schema_name}: checking Geolocation.position vs mapbox_id "
                f"(threshold_m={threshold_meters}, limit={limit})…"
            )
            stats = find_geolocation_mapbox_position_mismatches(
                threshold_meters=threshold_meters,
                limit=limit,
                progress_every=progress_every,
                print_missing_coords=print_missing_coords,
            )
            print(f"{tenant.schema_name}: done: {stats}")
