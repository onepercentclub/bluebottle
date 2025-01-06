from builtins import object

from django.conf import settings
from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework_json_api.serializers import ModelSerializer
from staticmaps_signature import StaticMapURLSigner
from timezonefinder import TimezoneFinder

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.geo.models import Country, Location, Place, Geolocation

staticmap_url_signer = StaticMapURLSigner(
    public_key=settings.STATIC_MAPS_API_KEY, private_key=settings.STATIC_MAPS_API_SECRET
)

tf = TimezoneFinder()


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
        "https://maps.googleapis.com/maps/api/staticmap"
        "?center={latitude},{longitude}&zoom=10&size=422x422"
        "&maptype=roadmap&markers={latitude},{longitude}&sensor=false"
        "&style=feature:poi|visibility:off&style=feature:poi.park|visibility:on"
    )

    def to_representation(self, value):
        try:
            latitude = value.latitude
            longitude = value.longitude
        except AttributeError:
            latitude = value.coords[1]
            longitude = value.coords[0]

        url = self.url.format(latitude=latitude, longitude=longitude)

        return staticmap_url_signer.sign_url(url)


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
