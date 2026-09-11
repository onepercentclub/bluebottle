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


class IdentifierField(serializers.Field):
    def get_attribute(self, instance):
        identifier = getattr(instance, 'identifier', None)
        if identifier:
            return identifier
        mapbox_id = getattr(instance, 'mapbox_id', None)
        geofeature = getattr(instance, 'geofeature', None)
        if geofeature and getattr(geofeature, 'mapbox_id', None):
            mapbox_id = geofeature.mapbox_id
        if not mapbox_id:
            return []
        return [{
            'type': 'PropertyValue',
            'propertyID': 'mapbox-feature-id',
            'value': mapbox_id,
        }]

    def to_representation(self, value):
        return [
            item for item in (normalize_identifier(entry) for entry in (value or []))
            if item
        ]

    def to_internal_value(self, data):
        if not data:
            return []
        if isinstance(data, dict):
            data = [data]
        if not isinstance(data, list):
            raise serializers.ValidationError('Expected a list of identifiers')
        return [
            item for item in (normalize_identifier(entry) for entry in data)
            if item
        ]


def normalize_identifier(item):
    if not isinstance(item, dict):
        return None
    property_id = item.get('propertyID') or item.get('property_id')
    value = item.get('value')
    if not property_id or value in (None, ''):
        return None
    return {
        'type': 'PropertyValue',
        'propertyID': property_id,
        'value': value,
    }
