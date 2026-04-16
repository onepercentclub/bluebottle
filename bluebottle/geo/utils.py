import requests
from django.conf import settings
from parler.utils.context import switch_language

from bluebottle.geo.models import GeoFeature, PLACE_TYPE_ORDER
from bluebottle.utils.models import Language


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


def collect_geo_features(geolocation):
    if not geolocation.mapbox_id:
        return 0

    current_place_type = geolocation.mapbox_id.split('.')[0]
    if current_place_type not in PLACE_TYPE_ORDER:
        return 0

    place_types = PLACE_TYPE_ORDER[: PLACE_TYPE_ORDER.index(current_place_type) + 1]
    parent_place_types = place_types[:-1]

    languages = Language.objects.values_list('code', flat=True)

    def upsert_feature(feature, force_place_type=None, force_update=False):
        mapbox_id = feature.get('properties', {}).get('mapbox_id') or feature.get('id')
        if not mapbox_id:
            return None, False
        place_type = force_place_type or (feature.get('place_type') or [None])[0] or (
            feature.get('properties') or {}
        ).get('feature_type') or current_place_type
        geo_feature, created = GeoFeature.objects.get_or_create(
            mapbox_id=mapbox_id,
            defaults={
                'code': (feature.get('properties') or {}).get('short_code'),
                'place_type': place_type,
            },
        )

        # Ensure place_type is correct for the selected feature even if it existed already.
        if geo_feature.place_type != place_type:
            geo_feature.place_type = place_type
            geo_feature.save(update_fields=['place_type'])

        # For selected features (especially addresses), we want to ensure we keep
        # the canonical Mapbox values even if the record already existed.
        should_update = created or force_update

        if should_update:
            for language in languages:
                with switch_language(geo_feature, language):
                    text_value = feature.get(f'text_{language}') or feature.get('text')
                    place_name_value = feature.get(f'place_name_{language}') or feature.get('place_name')
                    geo_feature.name = text_value
                    geo_feature.place_name = place_name_value or text_value

            # For address features Mapbox includes a housenumber in `address`.
            if force_update or not geo_feature.address:
                geo_feature.address = feature.get('address')

            geo_feature.save()

        return geo_feature, created

    created_or_linked = 0

    if not geolocation.position:
        return created_or_linked
    lon = geolocation.position[0]
    lat = geolocation.position[1]

    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
        f"{lon},{lat}.json"
    )

    if not parent_place_types:
        return created_or_linked

    response = requests.get(
        url,
        params={
            'access_token': settings.MAPBOX_API_KEY,
            'permanent': 'true',
            'language': ','.join(languages),
            'types': ','.join(parent_place_types),
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    for feature in data.get('features', []):
        place_type = (feature.get('place_type') or [None])[0]
        if place_type not in parent_place_types:
            continue

        geo_feature, _created = upsert_feature(feature)
        if not geo_feature:
            continue

        geolocation.features.add(geo_feature)
        created_or_linked += 1

    return created_or_linked
