from rest_framework import serializers
from bluebottle.geo.models import Location
from bluebottle.bluebottle_drf2.serializers import ImageSerializer

from .models import Country


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
