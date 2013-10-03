from rest_framework import serializers

from bluebottle.bluebottle_utils.validators import validate_postal_code
from bluebottle.bluebottle_utils.models import Address


class AddressSerializer(serializers.ModelSerializer):

    def validate_postal_code(self, attrs, source):
        value = attrs[source]
        if value:
            country_code = ''
            if 'country' in attrs:
                country_code = attrs['country']
            elif self.object and self.object.country:
                country_code = self.object.country.alpha2_code

            if country_code:
                validate_postal_code(value, country_code)
        return attrs

    class Meta:
        model = Address
        fields = ('id', 'line1', 'line2', 'city', 'state', 'country', 'postal_code')
