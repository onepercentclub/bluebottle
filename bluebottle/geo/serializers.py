from django.contrib.gis.geos import Point
from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.bluebottle_drf2.serializers import ImageSerializer
from bluebottle.geo.models import Country, Location, Place, InitiativePlace, Geolocation


class CountrySerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='alpha2_code')
    oda = serializers.BooleanField(source='oda_recipient')

    class Meta:
        model = Country
        fields = ('id', 'name', 'code', 'oda')


class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(source='position.latitude', max_digits=10, decimal_places=3)
    longitude = serializers.DecimalField(source='position.longitude', max_digits=10, decimal_places=3)
    image = ImageSerializer(required=False)

    class Meta:
        model = Location
        fields = ('id', 'name', 'description', 'image', 'latitude', 'longitude')


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = (
            'id', 'street', 'street_number', 'locality', 'province', 'country',
            'position', 'formatted_address',
        )


class InitiativeCountrySerializer(ModelSerializer):
    code = serializers.CharField(source='alpha2_code')
    oda = serializers.BooleanField(source='oda_recipient')

    class Meta:
        model = Country
        fields = ('id', 'name', 'code', 'oda')

    class JSONAPIMeta:
        resource_name = 'countries'


class InitiativePlaceSerializer(ModelSerializer):
    country = ResourceRelatedField(queryset=Country.objects.all())

    included_serializers = {
        'country': 'bluebottle.geo.serializers.InitiativeCountrySerializer',
    }

    class Meta:
        model = InitiativePlace
        fields = (
            'id', 'street', 'street_number', 'locality', 'province', 'country',
            'position', 'formatted_address',
        )

    class JSONAPIMeta:
        included_resources = ['country', ]
        resource_name = 'places'


class PointSerializer(serializers.CharField):

    def to_representation(self, instance):
        return {
            'latitude': instance.coords[1],
            'longitude': instance.coords[0]
        }

    def to_internal_value(self, data):
        if not data:
            return None
        try:
            point = Point(float(data['longitude']), float(data['latitude']))
        except ValueError as e:
            raise serializers.ValidationError("Invalid point. {}".format(e))
        return point


class GeolocationSerializer(ModelSerializer):
    position = PointSerializer()

    included_serializers = {
        'country': 'bluebottle.geo.serializers.InitiativeCountrySerializer'
    }

    class Meta:
        model = Geolocation
        fields = (
            'id', 'street', 'street_number',
            'locality', 'province',
            'country',
            'position',
            'formatted_address',
        )

    class JSONAPIMeta:
        included_resources = [
            'country',
            'position'
        ]
        resource_name = 'geolocations'
