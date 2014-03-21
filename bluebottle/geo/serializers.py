from rest_framework import serializers

from .models import Country


class CountrySerializer(serializers.ModelSerializer):
    code = serializers.CharField(source='alpha2_code')
    oda = serializers.BooleanField(source='oda_recipient')

    class Meta:
        model = Country
        fields = ('id', 'name', 'code', 'oda')
