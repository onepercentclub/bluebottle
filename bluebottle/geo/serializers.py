from builtins import object

from django.conf import settings
from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer
from timezonefinder import TimezoneFinder

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.geo.mapbox import FEATURE_TYPE_HIERARCHY
from bluebottle.geo.models import Country, Location, Place, Geolocation
from bluebottle.utils.utils import get_current_language

tf = TimezoneFinder()


def set_geofeature_language(geofeature, language=None):
    if not geofeature:
        return None
    language = (language or get_current_language() or 'en').split(',')[0]
    geofeature.set_current_language(language)
    return geofeature


def common_geofeature_for_geolocations(geolocations):
    """
    Most specific GeoFeature shared by all geolocations (same mapbox_id).

    For a single geolocation, returns its primary geofeature.
    """
    geolocations = [geolocation for geolocation in geolocations if geolocation]
    if not geolocations:
        return None
    if len(geolocations) == 1:
        return geolocations[0].geofeature

    feature_maps = []
    for geolocation in geolocations:
        by_type = {}
        for geofeature in geolocation.geofeatures.all():
            if geofeature.feature_type and geofeature.mapbox_id:
                by_type[geofeature.feature_type] = geofeature
        feature_maps.append(by_type)

    for feature_type in FEATURE_TYPE_HIERARCHY:
        features = [feature_map.get(feature_type) for feature_map in feature_maps]
        if any(feature is None for feature in features):
            continue
        if len({feature.mapbox_id for feature in features}) == 1:
            return features[0]
    return None


def activity_geolocation_display(geolocations, language=None):
    """
    Display fields for one or more activity geolocations.

    Uses the primary geofeature, or the most specific geofeature shared by all
    locations. Returns name/place_name in the active language only.
    """
    geolocations = [geolocation for geolocation in geolocations if geolocation]
    if not geolocations:
        return None

    geofeature = set_geofeature_language(
        common_geofeature_for_geolocations(geolocations),
        language=language,
    )
    if not geofeature:
        return None

    country = geolocations[0].country
    return {
        'locality': geofeature.name,
        'formattedAddress': geofeature.place_name,
        'country': {
            'code': country.alpha2_code if country else None,
        },
    }


# ---------------------------------------------------------------------------
# Activity card location formatting (geofeatures + card_location_display)
# ---------------------------------------------------------------------------

CARD_LOCATION_MODES = frozenset({
    'neighbourhood',
    'neighbourhood_city',
    'city',
    'city_region',
    'city_country',
})

CARD_LOCATION_COMMON_LEVEL_CHECKS = {
    'neighbourhood': (
        ('neighborhood',),
        ('locality',),
        ('city',),
        ('region',),
        ('country',),
    ),
    'neighbourhood_city': (
        ('neighborhood', 'city'),
        ('locality', 'city'),
        ('city',),
        ('region',),
        ('country',),
    ),
    'city': (
        ('city',),
        ('region',),
        ('country',),
    ),
    'city_region': (
        ('city', 'region'),
        ('region',),
        ('country',),
    ),
    'city_country': (
        ('city', 'country'),
        ('region', 'country'),
        ('country',),
    ),
}


def _card_attr(entry, key, default=None):
    if entry is None:
        return default
    if isinstance(entry, dict):
        return entry.get(key, default)
    return getattr(entry, key, default)


def _card_entries_for_language(entries, language):
    if not isinstance(language, str):
        language = 'en'

    matched = [
        entry for entry in entries
        if _card_attr(entry, 'language') == language
    ]
    if matched:
        return matched

    prefix = language.split('-')[0]
    return [
        entry for entry in entries
        if _card_attr(entry, 'language', '').startswith(prefix)
    ]


def _feature_name(geofeatures, feature_type):
    feature = next(
        (
            item for item in geofeatures
            if _card_attr(item, 'feature_type') == feature_type
        ),
        None,
    )
    return _card_attr(feature, 'name') if feature else None


def _card_location_parts(activity, language_geofeatures, language):
    place = _feature_name(language_geofeatures, 'place')
    locality = _feature_name(language_geofeatures, 'locality')
    city = place or locality

    country_feature = next(
        (
            item for item in language_geofeatures
            if _card_attr(item, 'feature_type') == 'country'
        ),
        None,
    )
    country = (
        _card_attr(country_feature, 'name')
        or _card_attr(country_feature, 'place_name')
        or next(
            (
                _card_attr(item, 'country')
                for item in language_geofeatures
                if _card_attr(item, 'country')
            ),
            None,
        )
    )
    if not country:
        countries = _card_entries_for_language(
            getattr(activity, 'country', None) or [],
            language,
        )
        if countries:
            country = _card_attr(countries[0], 'name')

    country_code = (
        _card_attr(country_feature, 'country_code')
        or next(
            (
                _card_attr(item, 'country_code')
                for item in language_geofeatures
                if _card_attr(item, 'country_code')
            ),
            None,
        )
    )

    return {
        'neighborhood': _feature_name(language_geofeatures, 'neighborhood'),
        'locality': locality,
        'city': city,
        'region': _feature_name(language_geofeatures, 'region'),
        'country': country,
        'country_code': country_code,
    }


def format_card_location_from_parts(mode, parts):
    if mode not in CARD_LOCATION_MODES:
        return None

    country = parts.get('country')
    country_code = parts.get('country_code')
    country_label = country or country_code
    country_abbrev = country_code or country

    if mode == 'neighbourhood':
        return (
            parts.get('neighborhood')
            or parts.get('city')
            or parts.get('region')
            or country
            or country_code
        )

    if mode == 'neighbourhood_city':
        neighborhood = parts.get('neighborhood')
        locality = parts.get('locality')
        city = parts.get('city')
        if neighborhood and city:
            return '{}, {}'.format(neighborhood, city)
        if locality and city and locality != city:
            return '{}, {}'.format(locality, city)
        if city:
            return city
        if locality:
            return locality
        if neighborhood:
            return neighborhood
        return parts.get('region') or country_label or country_code

    if mode == 'city':
        return parts.get('city') or parts.get('region') or country or country_code

    if mode == 'city_region':
        city = parts.get('city')
        region = parts.get('region')
        if city and region:
            return '{}, {}'.format(city, region)
        if region:
            return region
        return country_label

    if mode == 'city_country':
        city = parts.get('city')
        region = parts.get('region')
        if city and country_abbrev:
            return '{}, {}'.format(city, country_abbrev)
        if region and country_abbrev:
            return '{}, {}'.format(region, country_abbrev)
        return country_label

    return None


def format_card_location_from_values(mode, **kwargs):
    return format_card_location_from_parts(mode, kwargs)


def card_location_parts_from_geofeatures(activity, geofeatures, language):
    if not geofeatures:
        return None
    language_geofeatures = _card_entries_for_language(geofeatures, language)
    if not language_geofeatures:
        return None
    return _card_location_parts(activity, language_geofeatures, language)


def format_card_location(activity, card_location_display, language, geofeatures=None):
    if card_location_display not in CARD_LOCATION_MODES:
        return None

    if geofeatures is None:
        geofeatures = getattr(activity, 'geofeature', None)
    if not geofeatures:
        return None

    language_geofeatures = _card_entries_for_language(geofeatures, language)
    if not language_geofeatures:
        return None

    return format_card_location_from_parts(
        card_location_display,
        _card_location_parts(activity, language_geofeatures, language),
    )


def card_location_for_geolocation(geolocation, language=None, activity=None):
    from bluebottle.activities.documents import geofeatures_for_geolocation
    from bluebottle.initiatives.models import InitiativePlatformSettings

    language = (language or get_current_language() or 'en').split(',')[0]
    activity = activity or type('Activity', (), {'country': []})()
    return format_card_location(
        activity,
        InitiativePlatformSettings.load().card_location_display,
        language,
        geofeatures=geofeatures_for_geolocation(geolocation),
    )


def _common_parts_for_keys(all_parts, keys):
    if not all_parts:
        return None

    merged = {
        'neighborhood': None,
        'locality': None,
        'city': None,
        'region': None,
        'country': None,
        'country_code': None,
    }

    for key in keys:
        if key == 'country':
            country_keys = [
                part.get('country_code') or part.get('country')
                for part in all_parts
            ]
            if any(not value for value in country_keys) or len(set(country_keys)) != 1:
                return None
            merged['country'] = all_parts[0].get('country')
            merged['country_code'] = all_parts[0].get('country_code')
        else:
            values = [part.get(key) for part in all_parts if part]
            if any(not value for value in values) or len(set(values)) != 1:
                return None
            merged[key] = values[0]

    return merged


def format_common_card_location(activity, card_location_display, language, location_parts):
    if card_location_display not in CARD_LOCATION_MODES or not location_parts:
        return None

    for keys in CARD_LOCATION_COMMON_LEVEL_CHECKS.get(card_location_display, ()):
        common_parts = _common_parts_for_keys(location_parts, keys)
        if not common_parts:
            continue
        formatted = format_card_location_from_parts(card_location_display, common_parts)
        if formatted:
            return formatted
    return None


class PointSerializer(serializers.CharField):

    def to_representation(self, instance):
        return {
            'longitude': instance.coords[0],
            'latitude': instance.coords[1]
        }

    def to_internal_value(self, data):
        if not data:
            return None
        try:
            point = Point(float(data['longitude']), float(data['latitude']))
        except ValueError as e:
            raise serializers.ValidationError("Invalid point. {}".format(e))
        return point


class StaticMapsField(serializers.ReadOnlyField):
    url = (
        'https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/'
        'pin-s+3bb2d0({longitude},{latitude})/'
        '{longitude},{latitude},10/422x422'
        '?access_token={access_token}'
    )

    def to_representation(self, value):
        try:
            latitude = value.latitude
            longitude = value.longitude
        except AttributeError:
            latitude = value.coords[1]
            longitude = value.coords[0]

        return self.url.format(
            latitude=latitude,
            longitude=longitude,
            access_token=settings.MAPBOX_API_KEY,
        )


class CountrySerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='alpha2_code')
    oda = serializers.BooleanField(source='oda_recipient')

    class Meta(object):
        model = Country
        fields = ('id', 'name', 'code', 'oda')


class OfficeListSerializer(ModelSerializer):

    class Meta(object):
        model = Location
        fields = ('id', 'name', 'description', 'subregion')

    class JSONAPIMeta(object):
        resource_name = 'locations'
        included_resources = [
            'subregion',
            'subregion.region'
        ]

    included_serializers = {
        'subregion': 'bluebottle.offices.serializers.SubregionSerializer',
        'subregion.region': 'bluebottle.offices.serializers.RegionSerializer'
    }


class OfficeSerializer(ModelSerializer):
    latitude = serializers.DecimalField(source='position.latitude', required=False, max_digits=10, decimal_places=3)
    longitude = serializers.DecimalField(source='position.longitude', required=False, max_digits=10, decimal_places=3)
    image = ImageSerializer(required=False)

    static_map_url = StaticMapsField(source='position')

    class Meta(object):
        model = Location
        fields = (
            'id', 'name', 'description', 'image',
            'latitude', 'longitude', 'static_map_url',
            'subregion'
        )

    class JSONAPIMeta(object):
        resource_name = 'locations'
        included_resources = [
            'subregion',
            'subregion.region'
        ]

    included_serializers = {
        'subregion': 'bluebottle.offices.serializers.SubregionSerializer',
        'subregion.region': 'bluebottle.offices.serializers.RegionSerializer'
    }


class PlaceSerializer(ModelSerializer):
    position = PointSerializer(required=False, allow_null=True)

    class Meta(object):
        model = Place
        fields = (
            'id', 'street', 'street_number', 'postal_code',
            'locality', 'province', 'country', 'position', 'formatted_address',
            'mapbox_id'
        )

    class JSONAPIMeta(object):
        resource_name = 'places'
        included_resources = [
            'country',
        ]

    included_serializers = {
        'country': 'bluebottle.geo.serializers.InitiativeCountrySerializer',
    }


class SimplePointSerializer(serializers.CharField):

    def to_representation(self, instance):
        return [
            instance.coords[1],
            instance.coords[0]
        ]

    def to_internal_value(self, data):
        if not data:
            return None
        try:
            point = Point(float(data[1]), float(data[0]))
        except ValueError as e:
            raise serializers.ValidationError("Invalid point. {}".format(e))
        return point


class OldPlaceSerializer(serializers.ModelSerializer):
    position = SimplePointSerializer(required=False, allow_null=True)

    class Meta(object):
        model = Place
        fields = (
            'id', 'street', 'postal_code', 'street_number', 'locality', 'province', 'country',
            'position', 'formatted_address',
        )


class InitiativeCountrySerializer(ModelSerializer):
    code = serializers.CharField(source='alpha2_code')
    oda = serializers.BooleanField(source='oda_recipient')

    class Meta(object):
        model = Country
        fields = ('id', 'name', 'code', 'oda')

    class JSONAPIMeta(object):
        resource_name = 'countries'


class TinyPointSerializer(serializers.CharField):

    def to_representation(self, instance):
        if not hasattr(instance, 'coords'):
            return (instance.latitude, instance.longitude)
        else:
            return [instance.coords[1], instance.coords[0]]


class GeolocationSerializer(ModelSerializer):
    position = PointSerializer()
    static_map_url = StaticMapsField(source='position')
    timezone = serializers.ReadOnlyField()
    formatted_address = serializers.SerializerMethodField()
    locality = serializers.SerializerMethodField()

    def create(self, validated_data):
        mapbox_id = validated_data.get('mapbox_id')
        if mapbox_id:
            geolocation = Geolocation.objects.filter(mapbox_id=mapbox_id).first()
            if geolocation:
                return geolocation
        return super(GeolocationSerializer, self).create(validated_data)

    def _geofeature(self, obj):
        return set_geofeature_language(obj.geofeature)

    def get_formatted_address(self, obj):
        geofeature = self._geofeature(obj)
        if geofeature:
            return geofeature.place_name
        return obj.formatted_address

    def get_locality(self, obj):
        geofeature = self._geofeature(obj)
        if geofeature:
            return geofeature.name
        return obj.locality

    included_serializers = {
        'country': 'bluebottle.geo.serializers.InitiativeCountrySerializer'
    }

    class Meta(object):
        model = Geolocation
        fields = (
            'id',
            'street',
            'street_number',
            'locality',
            'province',
            'country',
            'position',
            'static_map_url',
            'formatted_address',
            'timezone',
            'mapbox_id'
        )

    class JSONAPIMeta(object):
        included_resources = [
            'country',
            'position'
        ]
        resource_name = 'geolocations'
