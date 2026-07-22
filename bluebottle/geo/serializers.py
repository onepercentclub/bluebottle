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


def card_location_for_geolocation(geolocation, language=None, activity=None):
    display = activity_geolocation_display([geolocation], language=language)
    if not display:
        return None
    return display['formattedAddress']


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
