from rest_framework import serializers


class ActivityPubIdField(serializers.CharField):
    def __init__(self):
        super().__init__(source='iri', required=False, allow_null=True)

    def get_attribute(self, instance):
        result = super().get_attribute(instance)
        if result:
            return result
        else:
            return instance.pub_url


class FederatedIdField(serializers.CharField):
    def __init__(self):
        super().__init__(source='*')

    def to_representation(self, value):
        if hasattr(value, 'origin') and value.origin:
            return value.origin.pub_url

        if hasattr(value, 'activity_pub_model') and value.activity_pub_model:
            return value.activity_pub_model.pub_url

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


def mapbox_id_from_federated_identifiers(identifiers):
    for item in identifiers or []:
        if not isinstance(item, dict):
            continue
        property_id = item.get('propertyID') or item.get('property_id')
        value = item.get('value')
        if property_id == 'mapbox-feature-id' and value:
            return value
    return None


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
    property_id = item.get('propertyID')
    value = item.get('value')
    if not property_id or value in (None, ''):
        return None
    return {
        'type': 'PropertyValue',
        'propertyID': property_id,
        'value': value,
    }


class MapboxIdField(IdentifierField):
    def to_internal_value(self, data):
        return mapbox_id_from_federated_identifiers(super().to_internal_value(data))
