from HTMLParser import HTMLParser
import re
from moneyed import Money

from rest_framework import serializers

from .validators import validate_postal_code
from .models import Address, Language


class MoneySerializer(serializers.DecimalField):

    def __init__(self,  max_digits=12, decimal_places=2, **kwargs):
        super(MoneySerializer, self).__init__(
            max_digits=max_digits,
            decimal_places=decimal_places,
            **kwargs
        )

    def to_representation(self, instance):
        return instance.amount

    def to_internal_value(self, data):
        if not data:
            return data

        if isinstance(data, int):
            return Money(data, 'EUR')
        else:
            return Money(data['amount'], data['currency'])


class MoneyTotalSerializer(serializers.ListField):
    """
    Serialize money totals with multiple currencies, e.g.
    [(450, 'EUR'), (23050, 'XEF')]
    """
    child = MoneySerializer()


class ShareSerializer(serializers.Serializer):
    share_name = serializers.CharField(max_length=256, required=True)
    share_email = serializers.EmailField(required=True)
    share_motivation = serializers.CharField(default="")
    share_cc = serializers.BooleanField(default=False)

    project = serializers.CharField(max_length=256, required=True)


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('id', 'code', 'language_name', 'native_name')


class MLStripper(HTMLParser):
    """ Used to strip HTML tags for meta fields (e.g. description) """

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


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
        fields = (
            'id', 'line1', 'line2', 'city', 'state', 'country', 'postal_code')


SCHEME_PATTERN = r'^https?://'


class URLField(serializers.URLField):
    """ URLField allowing absence of url scheme """

    def to_internal_value(self, value):
        """ Allow exclusion of http(s)://, add it if it's missing """
        if not value:
            return None
        m = re.match(SCHEME_PATTERN, value)
        if not m:  # no scheme
            value = "http://%s" % value
        return value

