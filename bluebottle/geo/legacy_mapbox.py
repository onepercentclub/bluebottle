"""
Legacy v5 mapbox id upgrade — used by sync_geolocation and migration scripts.
"""
import re

from django.conf import settings

from bluebottle.geo.mapbox import (
    feature_type_from_feature,
    forward_geocode,
    is_v6_id,
    mapbox_id_from_feature,
)

HOUSE_NUMBER_RE = re.compile(r'^\d+[A-Za-z]?$')
HOUSE_NUMBER_SEARCH_RE = re.compile(r'\b(\d+[A-Za-z]?)\b')

BROAD_FORWARD_TYPES = 'address,street,place,locality,postcode,district,region,country'
PARENT_CONTEXT_TYPES = ('place', 'locality', 'district', 'region', 'country', 'postcode')

LEGACY_ADDRESS_FORWARD_TYPES = BROAD_FORWARD_TYPES


def is_legacy_id(value):
    return bool(value) and not is_v6_id(str(value))


is_legacy_mapbox_id = is_legacy_id


def extract_house_number_from_address_fields(
    street_number=None,
    street=None,
    formatted_address=None,
):
    if street_number:
        candidate = str(street_number).strip()
        if HOUSE_NUMBER_RE.match(candidate):
            return candidate

    if street:
        match = HOUSE_NUMBER_SEARCH_RE.search(str(street).strip())
        if match:
            return match.group(1)

    if formatted_address:
        first_line = str(formatted_address).split(',')[0].strip()
        if first_line:
            matches = list(HOUSE_NUMBER_SEARCH_RE.finditer(first_line))
            if matches:
                return matches[-1].group(1)

    return None


def _v6_id_from_feature(feature):
    mapbox_id = mapbox_id_from_feature(feature)
    if mapbox_id and is_v6_id(str(mapbox_id)):
        return str(mapbox_id)
    return None


def _address_forward_query(geolocation):
    house_number = extract_house_number_from_address_fields(
        street_number=geolocation.street_number,
        street=geolocation.street,
        formatted_address=geolocation.formatted_address,
    )
    parts = []
    street_line = (geolocation.street or '').strip()
    if not street_line and geolocation.formatted_address:
        street_line = str(geolocation.formatted_address).split(',')[0].strip()
    if street_line:
        if house_number and house_number not in street_line:
            parts.append(f'{street_line} {house_number}')
        else:
            parts.append(street_line)
    if geolocation.locality:
        parts.append(str(geolocation.locality))
    if geolocation.country_id:
        parts.append(geolocation.country.name)
    elif geolocation.province:
        parts.append(str(geolocation.province))
    return ', '.join(part for part in parts if part)


def upgrade_mapbox_id(geolocation):
    """Upgrade a legacy v5 mapbox_id on geolocation to a permanent v6 id."""
    mapbox_id = geolocation.mapbox_id
    if not mapbox_id or not settings.MAPBOX_API_KEY:
        return mapbox_id

    if is_v6_id(mapbox_id):
        return mapbox_id

    position = None
    if geolocation.position:
        position = (geolocation.position.x, geolocation.position.y)

    new_id = _v6_id_from_feature(forward_geocode(q=mapbox_id, permanent=True)) or mapbox_id

    if mapbox_id.startswith('address.') and not is_v6_id(new_id):
        query = _address_forward_query(geolocation)
        kwargs = {'q': query, 'types': 'address', 'permanent': True}
        if position:
            kwargs['proximity_lon'], kwargs['proximity_lat'] = position
        feature = forward_geocode(**kwargs) if query else None
        if not feature:
            feature = forward_geocode(q=query or mapbox_id, types=BROAD_FORWARD_TYPES, permanent=True)

        has_house_number = bool(extract_house_number_from_address_fields(
            street_number=geolocation.street_number,
            street=geolocation.street,
            formatted_address=geolocation.formatted_address,
        ))
        resolved = _v6_id_from_feature(feature)
        if not has_house_number and feature:
            resolved_type = feature_type_from_feature(feature)
            if resolved_type in ('street', 'address'):
                context = (feature.get('properties') or {}).get('context') or {}
                for place_type in PARENT_CONTEXT_TYPES:
                    ctx_id = (context.get(place_type) or {}).get('mapbox_id')
                    if ctx_id and is_v6_id(str(ctx_id)):
                        resolved = str(ctx_id)
                        break
        if resolved:
            new_id = resolved

    if new_id != mapbox_id:
        geolocation.mapbox_id = new_id
        if geolocation.pk:
            from bluebottle.geo.models import Geolocation
            Geolocation.objects.filter(pk=geolocation.pk).update(mapbox_id=new_id)

    return geolocation.mapbox_id
