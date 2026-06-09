"""
Low-level Mapbox Geocoding API helpers (v6 forward and reverse).
"""
import math

import requests
from django.conf import settings

V6_FORWARD_URL = 'https://api.mapbox.com/search/geocode/v6/forward'
V6_REVERSE_URL = 'https://api.mapbox.com/search/geocode/v6/reverse'


def haversine_km(*, lon1, lat1, lon2, lat2):
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


def coords_from_feature(feature):
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


def is_v6_id(value):
    return bool(value) and (str(value).startswith('dXJu') or str(value).startswith('urn:'))


def mapbox_id_from_feature(feature):
    if not isinstance(feature, dict):
        return None
    props = feature.get('properties') or {}
    return feature.get('id') or props.get('mapbox_id')


def feature_type_from_feature(feature):
    if not isinstance(feature, dict):
        return None
    props = feature.get('properties') or {}
    place_types = feature.get('place_type') or []
    return props.get('feature_type') or (place_types[0] if place_types else None)


def forward_geocode(
    *,
    q,
    proximity_lon=None,
    proximity_lat=None,
    types=None,
    languages=None,
    permanent=True,
):
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


v6_forward_first_feature = forward_geocode


def reverse_geocode(*, longitude, latitude, types=None, languages=None, permanent=True):
    access_token = settings.MAPBOX_API_KEY
    if not access_token:
        return None

    params = {
        'longitude': longitude,
        'latitude': latitude,
        'access_token': access_token,
        'limit': 5,
    }
    if permanent:
        params['permanent'] = 'true'
    if types:
        params['types'] = types
    if languages:
        params['language'] = languages

    response = requests.get(V6_REVERSE_URL, params=params, timeout=30)
    if response.status_code != 200:
        return None

    features = (response.json() or {}).get('features') or []
    return features[0] if features else None


def reverse_geocode_position(position):
    if not position:
        return None
    lon, lat = position.coords
    return reverse_geocode(longitude=lon, latitude=lat)


v6_reverse_first_feature = reverse_geocode


def geocode_by_id(mapbox_id):
    return forward_geocode(q=mapbox_id, permanent=True)


def resolve_mapbox_id_coords(mapbox_id):
    if not mapbox_id:
        return None
    try:
        feature = forward_geocode(q=mapbox_id)
        return coords_from_feature(feature) if feature else None
    except Exception:
        return None
