from django.db import connection

from rest_framework import serializers
from rest_framework.reverse import reverse


class ActivityPubIdField(serializers.CharField):
    def __init__(self, url_name):
        self.url_name = url_name

        super().__init__(source='*', required=False)

    def to_representation(self, instance):
        if instance.iri:
            return instance.iri
        else:
            return connection.tenant.build_absolute_url(
                reverse(self.url_name, args=(instance.pk, ))
            )

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        return {'id': result}


class FederatedIdField(serializers.CharField):
    def __init__(self, url_name):
        self.url_name = url_name
        super().__init__(source='*')

    def to_representation(self, value):
        return value.activity_pub_url

    def to_internal_value(self, value):
        return {'id': value}


class TypeValidator:
    requires_context = True

    def __call__(self, value, serialized_field):
        return value == serialized_field.type


class TypeField(serializers.CharField):
    def __init__(self, type, *args, **kwargs):
        self.type = type

        kwargs['validators'] = kwargs.pop('validators', []) + [TypeValidator()]
        kwargs['required'] = False
        kwargs['source'] = '*'

        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        return self.type

    def to_internal_value(self, value):
        return {'type': self.type}
