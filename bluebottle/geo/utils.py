import requests
import re
from typing import Optional, Tuple
from django.conf import settings
from parler.utils.context import switch_language

from bluebottle.geo.models import GeoFeature
from bluebottle.utils.models import Language

try:
    from addressformatting import AddressFormatter
except ImportError:  # pragma: no cover
    AddressFormatter = None


def pick_preferred_reverse_geocode_feature(features):
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
                for f in features:
                    if (f.get('place_type') or [None])[0] == preferred:
                        return f
    return first


def extract_house_number_from_address_fields(
    street_number: Optional[str] = None,
    street: Optional[str] = None,
    formatted_address: Optional[str] = None,
) -> Optional[str]:
    if street_number:
        candidate = str(street_number).strip()
        if re.match(r"^\d+[A-Za-z]?$", candidate):
            return candidate
    if street:
        s = str(street).strip()
        m = re.search(r"\b(\d+[A-Za-z]?)\b", s)
        if m:
            return m.group(1)
    if formatted_address:
        first_line = str(formatted_address).split(",")[0].strip()
        if first_line:
            matches = list(re.finditer(r"\b(\d+[A-Za-z]?)\b", first_line))
            if matches:
                return matches[-1].group(1)
    return None


def normalize_mapbox_id(
    *,
    mapbox_id: Optional[str],
    street: Optional[str] = None,
    street_number: Optional[str] = None,
    formatted_address: Optional[str] = None,
    locality: Optional[str] = None,
    province: Optional[str] = None,
    country_name: Optional[str] = None,
    position: Optional[Tuple[float, float]] = None,  # (lon, lat)
    access_token: Optional[str] = None,
) -> Optional[str]:
    """
    Normalize legacy v5-style ids ("place.123", "address.456") to modern v6 ids (URN/hash).
    Returns the new id, or the original when it can't be resolved.
    """
    if not mapbox_id:
        return None

    token = access_token or settings.MAPBOX_API_KEY
    if not token:
        return mapbox_id

    current = str(mapbox_id).strip()

    def is_modern(value: str) -> bool:
        return value.startswith("dXJu") or value.startswith("urn:")

    def v6_forward(params):
        response = requests.get(
            "https://api.mapbox.com/search/geocode/v6/forward",
            params={**params, "access_token": token, "limit": 1},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json() or {}
        features = payload.get("features") or []
        return features[0] if features else None

    # If it looks like a legacy id, try resolving it directly via v6.
    if "." in current and not is_modern(current):
        resolved = v6_forward({"q": current, "permanent": "true"})
        resolved_id = (resolved or {}).get("id")
        if resolved_id and is_modern(resolved_id):
            current = resolved_id

    # Special-case legacy address ids: resolve via a better address query.
    if mapbox_id.startswith("address.") and not is_modern(current):
        house_number = extract_house_number_from_address_fields(
            street_number=street_number,
            street=street,
            formatted_address=formatted_address,
        )
        query_parts = []
        street_line = str(street).strip() if street else ""
        if not street_line and formatted_address:
            street_line = str(formatted_address).split(",")[0].strip()
        if street_line:
            if house_number and house_number not in street_line:
                query_parts.append(f"{street_line} {house_number}")
            else:
                query_parts.append(street_line)
        if locality:
            query_parts.append(str(locality))
        if country_name:
            query_parts.append(str(country_name))
        elif province:
            query_parts.append(str(province))

        q = ", ".join([p for p in query_parts if p])
        if q:
            params = {"q": q, "types": "address", "permanent": "true"}
            if position:
                params["proximity"] = f"{position[0]},{position[1]}"
            resolved = v6_forward(params)
            resolved_id = (resolved or {}).get("id")
            if resolved_id and is_modern(resolved_id):
                current = resolved_id

    return current


def collect_geo_features(geolocation):
    if not geolocation.mapbox_id:
        return 0

    # Fallback: some ids are still in "{type}.{id}" format (e.g. postcode.*)
    current_place_type = geolocation.mapbox_id.split('.')[0]

    languages = Language.objects.values_list('code', flat=True)
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
                'road': (props.get('street_name') or feature.get('text') or props.get('name')),
                'city': place_name,
                'postcode': postcode_name,
                'state': region_name,
                'country': country_name,
            }
        elif place_type in ('neighborhood',):
            address = {
                'road': name,
                'city': place_name,
                'state': region_name,
                'country': country_name,
            }
        elif place_type in ('district',):
            address = {
                'road': name,
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

        # Remove empty values
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

        geo_feature, created = GeoFeature.objects.get_or_create(
            mapbox_id=mapbox_id,
            defaults={
                'code': props.get('short_code'),
                'place_type': place_type,
            },
        )

        if geo_feature.place_type != place_type:
            geo_feature.place_type = place_type
            geo_feature.save(update_fields=['place_type'])

        should_update = created or force_update

        if should_update:
            translations = feature.get('translations') or {}
            for language in languages:
                with switch_language(geo_feature, language):
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
                    geo_feature.name = text_value
                    geo_feature.place_name = place_name_value or text_value
            geo_feature.save()

        return geo_feature, created

    # Use v6 forward geocoding to retrieve by mapbox_id and get its parent context.
    response = requests.get(
        "https://api.mapbox.com/search/geocode/v6/forward",
        params={
            'q': geolocation.mapbox_id,
            'access_token': settings.MAPBOX_API_KEY,
            'permanent': 'true',
            'language': ",".join(languages),
            'limit': 1,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    features = data.get('features') or []
    if not features:
        return 0

    selected = features[0]
    context = (selected.get('properties') or {}).get('context') or {}
    created_or_linked = 0

    # Persist parents from v6 context hierarchy, up to (but excluding) the selected type.
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
            ctx_feature, force_place_type=place_type, force_update=True
        )
        if not geo_feature:
            continue
        geolocation.features.add(geo_feature)
        created_or_linked += 1

    return created_or_linked
