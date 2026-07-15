from bluebottle.geo.models import GeoFeature


def ensure_geolocation_geofeatures(geolocation):
    if geolocation.geofeatures.exists():
        return geolocation

    place_name = geolocation.locality
    if not place_name:
        return geolocation

    place = GeoFeature.objects.create(
        mapbox_id='test-place-{}-{}'.format(geolocation.pk, place_name),
        feature_type='place',
    )
    place.set_current_language('en')
    place.name = place_name
    place.place_name = place_name
    place.save()

    features = [place]
    country = geolocation.country
    if country:
        country_feature, created = GeoFeature.objects.get_or_create(
            mapbox_id='test-country-{}'.format(country.alpha2_code),
            defaults={'feature_type': 'country'},
        )
        if created or not country_feature.translations.filter(language_code='en').exists():
            country_feature.set_current_language('en')
            country_feature.name = country.name
            country_feature.place_name = country.name
            country_feature.save()
        features.append(country_feature)

    geolocation.geofeature = place
    geolocation.save(update_fields=['geofeature'], skip_mapbox_sync=True)
    geolocation.geofeatures.set(features)
    return geolocation
