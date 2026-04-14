import requests
from django.conf import settings
from parler.utils.context import switch_language

from bluebottle.geo.models import GeoFeature, PLACE_TYPE_ORDER


def collect_geo_features(geolocation):
    if not geolocation.position:
        return 0
    if not geolocation.mapbox_id:
        return 0

    current_place_type = geolocation.mapbox_id.split('.')[0]
    if current_place_type not in PLACE_TYPE_ORDER:
        return 0

    url = (
        f"https://api.mapbox.com/geocoding/v5/mapbox.places/"
        f"{geolocation.position.coords[0]},{geolocation.position.coords[1]}.json"
    )
    languages = ['nl', 'de', 'fr', 'en']

    response = requests.get(
        url,
        params={
            'access_token': settings.MAPBOX_API_KEY,
            'permanent': 'true',
            'language': ','.join(languages),
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    relevant_place_types = PLACE_TYPE_ORDER[
        : PLACE_TYPE_ORDER.index(current_place_type) + 1
    ]

    created_or_linked = 0
    for feature in data.get('features', []):
        mapbox_id = feature.get('properties', {}).get('mapbox_id')
        place_type = (feature.get('place_type') or [None])[0]
        if not mapbox_id or place_type not in relevant_place_types:
            continue

        geo_feature, created = GeoFeature.objects.get_or_create(
            mapbox_id=mapbox_id,
            defaults={
                'code': feature.get('properties', {}).get('short_code'),
                'place_type': place_type,
            },
        )

        if created:
            for language in languages:
                with switch_language(geo_feature, language):
                    geo_feature.name = feature.get(f'text_{language}') or feature.get(
                        'text'
                    )
            geo_feature.save()

        geolocation.features.add(geo_feature)
        created_or_linked += 1

    return created_or_linked

