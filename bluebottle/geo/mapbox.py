"""
Low-level Mapbox Geocoding API helpers (v5 reverse/id lookup, v6 forward).

Used by Geolocation save/sync, maintenance scripts, and GeoFeature collection.
"""
from __future__ import annotations

import math
from typing import Any, Optional, Tuple

import requests
from django.conf import settings

V6_FORWARD_URL = 'https://api.mapbox.com/search/geocode/v6/forward'


def haversine_km(*, lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Great-circle distance in km between two lon/lat points.

    Used by resolve_mapbox_mismatch and scripts/check_geolocation_mapbox_position.py.
    """
    r = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return r * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def coords_from_feature(feature: Any) -> Optional[Tuple[float, float]]:
    """Extract (lon, lat) from a Mapbox feature geometry.coordinates or center."""
    if not isinstance(feature, dict):
        return None
    geometry = feature.get('geometry') or {}
    coords = geometry.get('coordinates')
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        try:
            return float(coords[0]), float(coords[1])
        except (TypeError, ValueError):
            return None
    center = feature.get('center')
    if isinstance(center, (list, tuple)) and len(center) >= 2:
        try:
            return float(center[0]), float(center[1])
        except (TypeError, ValueError):
            return None
    return None


def is_modern_mapbox_id(value: str) -> bool:
    """Return True for permanent v6-style ids (dXJu… or urn:), as opposed to legacy v5 ids."""
    return value.startswith('dXJu') or value.startswith('urn:')


def mapbox_id_from_feature(feature: dict) -> Optional[str]:
    """Read the canonical mapbox id from a feature id or properties.mapbox_id."""
    if not isinstance(feature, dict):
        return None
    props = feature.get('properties') or {}
    return feature.get('id') or props.get('mapbox_id')


def feature_type_from_feature(feature: dict) -> Optional[str]:
    """Read place type (address, place, etc.) from feature properties or place_type."""
    if not isinstance(feature, dict):
        return None
    props = feature.get('properties') or {}
    place_types = feature.get('place_type') or []
    return props.get('feature_type') or (place_types[0] if place_types else None)


def pick_preferred_reverse_geocode_feature(features):
    """Pick the best reverse-geocode result; prefer parent place when address accuracy is low.

    Used by reverse_geocode_position before returning a v5 Places API feature.
    """
    if not features:
        return None
    first = features[0]
    first_type = (first.get('place_type') or [None])[0]
    props = first.get('properties') or {}
    accuracy = props.get('accuracy')
    if first_type == 'address':
        should_prefer_parent = (
            accuracy in ('interpolated', 'approximate', 'centroid')
            or not (props.get('address') or props.get('housenumber'))
        )
        if should_prefer_parent:
            for preferred in ('place', 'locality', 'district'):
                for feature in features:
                    if (feature.get('place_type') or [None])[0] == preferred:
                        return feature
    return first


def reverse_geocode_position(position) -> Optional[dict]:
    """Reverse-geocode a GIS point via Mapbox v5 Places API.

    Called from Geolocation.reverse_geocode and resolve_mapbox_mismatch.
    """
    access_token = settings.MAPBOX_API_KEY
    if not access_token or not position:
        return None

    lon, lat = position.coords
    url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{lon},{lat}.json'
    response = requests.get(url, params={'access_token': access_token}, timeout=30)
    if response.status_code != 200:
        return None

    data = response.json()
    features = data.get('features') or []
    if not features:
        return None
    return pick_preferred_reverse_geocode_feature(features)


def geocode_by_id(mapbox_id: str) -> Optional[dict]:
    """Look up a feature by permanent mapbox id via Mapbox v5 Places API.

    Called from Geolocation.geocode_by_id and resolve_mapbox_id_coords.
    """
    access_token = settings.MAPBOX_API_KEY
    if not access_token or not mapbox_id:
        return None

    url = f'https://api.mapbox.com/geocoding/v5/mapbox.places/{mapbox_id}.json'
    response = requests.get(url, params={'access_token': access_token}, timeout=30)
    if response.status_code != 200:
        return None

    features = (response.json() or {}).get('features') or []
    return features[0] if features else None


def v6_forward_first_feature(
    *,
    q: str,
    proximity_lon: Optional[float] = None,
    proximity_lat: Optional[float] = None,
    types: Optional[str] = None,
    languages: Optional[str] = None,
    permanent: bool = True,
) -> Optional[dict]:
    """Mapbox v6 forward geocode returning the top feature, or None.

    Used by geolocation mismatch resolution, id normalization, and collect_geo_features.
    """
    if not (q or '').strip():
        return None

    access_token = settings.MAPBOX_API_KEY
    if not access_token:
        return None

    params = {
        'q': q.strip(),
        'access_token': access_token,
        'limit': 1,
    }
    if permanent:
        params['permanent'] = 'true'
    if proximity_lon is not None and proximity_lat is not None:
        params['proximity'] = f'{proximity_lon},{proximity_lat}'
    if types:
        params['types'] = types
    if languages:
        params['language'] = languages

    response = requests.get(V6_FORWARD_URL, params=params, timeout=30)
    response.raise_for_status()
    features = (response.json() or {}).get('features') or []
    return features[0] if features else None


def resolve_mapbox_id_coords(mapbox_id: str) -> Optional[Tuple[float, float]]:
    """Resolve coordinates for a stored mapbox id (v5 id lookup, then v6 forward).

    Used by resolve_mapbox_mismatch and check_geolocation_mapbox_position.py.
    """
    if not mapbox_id:
        return None

    coords = coords_from_feature(geocode_by_id(mapbox_id))
    if coords:
        return coords

    try:
        feature = v6_forward_first_feature(q=mapbox_id)
        return coords_from_feature(feature) if feature else None
    except Exception:
        return None
