from rest_framework import serializers
from bluebottle.geo.models import Location

from .models import Country


class CountrySerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='alpha2_code')
    oda = serializers.BooleanField(source='oda_recipient')

    class Meta:
        model = Country
        fields = ('id', 'name', 'code', 'oda')


class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.DecimalField(source='position.latitude')
    longitude = serializers.DecimalField(source='position.longitude')

    class Meta:
        model = Location
        fields = ('id', 'name', 'latitude', 'longitude')
