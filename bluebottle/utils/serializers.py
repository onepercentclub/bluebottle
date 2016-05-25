from HTMLParser import HTMLParser
import sys
import re

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.template.defaultfilters import truncatechars
from importlib import import_module

from django_tools.middlewares import ThreadLocal
from rest_framework import serializers
from rest_framework.serializers import get_component
from taggit.managers import _TaggableManager

from bluebottle.bluebottle_drf2.serializers import ImageSerializer

from .validators import validate_postal_code
from .models import Address, Language


class ShareSerializer(serializers.Serializer):
    share_name = serializers.CharField(max_length=256, required=True)
    share_email = serializers.EmailField(required=True)
    share_motivation = serializers.CharField(default="", required=True)
    share_cc = serializers.BooleanField(default=False, required=True)

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

    def from_native(self, value):
        """ Allow exclusion of http(s)://, add it if it's missing """
        if not value:
            return value
        m = re.match(SCHEME_PATTERN, value)
        if not m:  # no scheme
            value = "http://%s" % value
        return value


class HumanReadableChoiceField(serializers.ChoiceField):
    def field_to_native(self, obj, field_name):
        """
        Given and object and a field name, returns the value that should be
        serialized for that field. Display the choice label.
        """
        if obj is None:
            return self.empty

        if self.source == '*':
            return self.to_native(obj)

        source = self.source or field_name
        value = obj

        components = source.split('.')
        for component in components:
            # last item, fetch human readable form
            if component == components[-1]:
                component = 'get_{0}_display'.format(component)
            value = get_component(value, component)
            if value is None:
                break

        return self.to_native(value.lower())

