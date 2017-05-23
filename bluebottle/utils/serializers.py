import json
from HTMLParser import HTMLParser
import re

from django.utils.translation import ugettext_lazy as _
from django.core.validators import BaseValidator
from moneyed import Money

from rest_framework import serializers

from .validators import validate_postal_code
from .models import Address, Language


class MaxAmountValidator(BaseValidator):
    compare = lambda self, a, b: a.amount > b
    message = _('Ensure this value is less than or equal to %(limit_value)s.')
    code = 'max_amount'


class MinAmountValidator(BaseValidator):
    compare = lambda self, a, b: a.amount < b
    message = _('Ensure this value is greater than or equal to %(limit_value)s.')
    code = 'min_amount'


class ProjectCurrencyValidator(object):
    """
    Validates that the currency of the field is the same as the projects currency
    """
    message = _('Currency does not match project any of the currencies')

    def __init__(self, fields=None, message=None):
        if fields is None:
            fields = ['amount']

        self.fields = fields
        self.message = message or self.message

    def __call__(self, data):
        for field in self.fields:
            if unicode(data[field].currency) not in data['project'].currencies:
                raise serializers.ValidationError(
                    _('Currency does not match project any of the currencies.')
                )


class MoneySerializer(serializers.DecimalField):
    default_error_messages = {
        'max_amount': _('Ensure this amount is less than or equal to {max_amount}.'),
        'min_amount': _('Ensure this amount is greater than or equal to {min_amount}.'),
    }

    def __init__(self, max_digits=12, decimal_places=2, max_amount=None, min_amount=None, **kwargs):
        super(MoneySerializer, self).__init__(
            max_digits=max_digits,
            decimal_places=decimal_places,
            **kwargs
        )
        if max_amount is not None:
            message = self.error_messages['max_amount'].format(max_amount=max_amount)
            self.validators.append(MaxAmountValidator(max_amount, message=message))

        if min_amount is not None:
            message = self.error_messages['min_amount'].format(min_amount=min_amount)
            self.validators.append(MinAmountValidator(min_amount, message=message))

    def to_representation(self, instance):
        return {
            'amount': instance.amount,
            'currency': str(instance.currency)
        }

    def to_internal_value(self, data):
        if not data:
            return data
        try:
            return Money(float(data), 'EUR')
        except ValueError:
            data = json.loads(data)
            return Money(data.get('amount', 0), data['currency'])
        except TypeError:
            return Money(data.get('amount', 0), data['currency'])


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
