from django.db import connection
import inflection
from rest_framework import serializers, exceptions

from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.processor import default_context, expand_iri
from bluebottle.activity_pub.serializers.fields import FederatedIdField, ActivityPubIdField, TypeField
from bluebottle.activity_pub.utils import is_local

from rest_polymorphic.serializers import PolymorphicSerializer


class ActivityPubListSerializer(serializers.ListSerializer):
    def get_value(self, data):
        result = super().get_value(data)

        if not isinstance(result, (tuple, list)):
            # In json-ld single items are compacted to lists. Make a list again in that case
            return [result]

        return result

    def create(self, validated_data):
        result = []
        for item in validated_data:
            instance = ActivityPubModel.objects.from_iri(item.get('id'))
            if instance:
                result.append(self.child.update(instance, item))
            else:
                result.append(self.child.create(item))

        return result

    def update(self, instances, validated_data):
        result = []
        for (instance, item) in zip(instances, validated_data):
            if instance:
                result.append(self.child.update(instance, item))
            else:
                result.append(self.child.create(item))

        return result


class ActivityPubSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        for attr_name, attr in attrs.items():
            if (
                isinstance(attr, serializers.Serializer) and
                not isinstance(
                    attr,
                    (BaseActivityPubSerializer, ActivityPubListSerializer)
                )
            ):
                raise TypeError(
                    f'Attribute {attr_name} should be a subclass of ActivityPubSerializer'
                )

        type_iri = None
        if 'Meta' in attrs and hasattr(attrs['Meta'], 'model'):
            if 'id' not in attrs or not isinstance(attrs['id'], ActivityPubIdField):
                raise TypeError(f'{name} is missing an IdField')

            if 'type' not in attrs or not isinstance(attrs['type'], TypeField):
                raise TypeError(f'{name} is missing a TypeField')

            type_iri = expand_iri(attrs['type'].type)
            if expand_iri(attrs['type'].type).startswith('_:'):
                raise TypeError(f'{attrs["type"].type} is not a correct ActivityPub type')

            for [attr, field] in attrs.items():
                if (
                    isinstance(field, (BaseActivityPubSerializer, serializers.Field)) and
                    attr not in ('id', 'type', )
                ):
                    if expand_iri(inflection.camelize(attr, False)).startswith('_:'):
                        raise TypeError(
                            f'{attr} is not a correct ActivityPub type'
                        )

        result = super().__new__(cls, name, bases, attrs)

        if type_iri:
            ActivityPubSerializer.serializer_mapping[result.Meta.model] = result

        return result


class ActivityPubSerializer(PolymorphicSerializer):
    serializer_mapping = {}
    model_serializer_mapping = {}
    resource_type_field_name = 'type'

    def __init__(self, *args, full=True, include=False, origin=None, **kwargs):
        super(PolymorphicSerializer, self).__init__(*args, **kwargs)

        self.resource_type_model_mapping = {}
        self.model_serializer_mapping = {}

        for model, serializer in self.serializer_mapping.items():
            resource_type = self.to_resource_type(model)
            if callable(serializer):
                serializer = serializer(
                    *args, full=full, include=include, origin=origin, **kwargs
                )
                serializer.parent = self

            self.resource_type_model_mapping[resource_type] = model
            self.model_serializer_mapping[model] = serializer

    def to_resource_type(self, model_or_instance):
        serializer = self.serializer_mapping[self._to_model(model_or_instance)]
        return serializer._declared_fields['type'].type

    def to_representation(self, instance):
        serializer = self._get_serializer_from_model_or_instance(instance)

        return serializer.to_representation(instance)

    @property
    def data(self):
        return super(serializers.Serializer, self).data


class BaseActivityPubSerializer(serializers.ModelSerializer, metaclass=ActivityPubSerializerMetaclass):
    def __init__(self, *args, full=True, include=False, origin=None, **kwargs):
        self.include = include
        self.full = full
        self.origin = origin

        super().__init__(*args, **kwargs)

    class Meta:
        list_serializer_class = ActivityPubListSerializer
        fields = ('type', 'id')

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if self.full:
            return representation
        else:
            if self.include:
                representation.pop('type', None)
                return representation
            else:
                return representation['id']

    def save(self, **kwargs):
        iri = self.validated_data.get('id', None)

        if iri:
            self.instance = self.Meta.model.objects.from_iri(iri)

        return super().save(**kwargs)

    def create(self, validated_data):
        iri = validated_data.get('iri')
        if iri and not is_local(iri):
            instance = self.Meta.model.objects.filter(iri=iri).first()
            if instance:
                return self.update(instance, validated_data)

        for name, field in self.fields.items():
            if name in validated_data and hasattr(field, 'save'):
                validated_data[name] = field.save(validated_data[name])

        validated_data.pop('type', None)
        if self.origin:
            validated_data['federated_object'] = self.origin

        return self.Meta.model.objects.create(**validated_data)

    def update(self, instance, validated_data):
        iri = validated_data.pop('iri', None)
        request = self.context.get('request')
        request_auth = getattr(request, 'auth', None)
        auth_iri = getattr(request_auth, 'iri', None)

        # Do not allow remote request to update local instances
        if (
            is_local(iri) and
            request_auth and
            auth_iri and
            not is_local(auth_iri)
        ):
            return instance

        for name, field in self.fields.items():
            if name in validated_data and hasattr(field, 'save'):
                validated_data[name] = field.save(validated_data[name])

        validated_data.pop('type', None)
        return super().update(instance, validated_data)

    def get_value(self, data):
        result = super().get_value(data)

        if isinstance(result, str):
            result = {'id': result}

        return result


class FederatedObjectListSerializer(serializers.ListSerializer):
    def get_value(self, data):
        result = super().get_value(data)

        if not isinstance(result, (tuple, list)):
            # In json-ld single items are compacted to lists. Make a list again in that case
            return [result]

        return result

    def update(self, instances, validated_data):
        result = []
        for index, instance in enumerate(instances):
            result.append(self.child.update(instance, validated_data[index]))

        return result


class FederatedObjectSerializer(PolymorphicSerializer):
    serializer_mapping = {}
    model_serializer_mapping = {}
    resource_type_field_name = 'type'

    def __init__(self, *args, origin=None, **kwargs):
        super(PolymorphicSerializer, self).__init__(*args, **kwargs)

        self.resource_type_model_mapping = {}
        self.model_serializer_mapping = {}

        for model, serializer in self.serializer_mapping.items():
            resource_type = self.to_resource_type(model)
            if callable(serializer):
                serializer = serializer(*args, origin=origin, **kwargs)
                serializer.parent = self

            self.resource_type_model_mapping[resource_type] = model
            self.model_serializer_mapping[model] = serializer

    def to_resource_type(self, model_or_instance):
        serializer = self.serializer_mapping[self._to_model(model_or_instance)]
        return serializer._declared_fields['type'].type

    def to_representation(self, instance):
        serializer = self._get_serializer_from_model_or_instance(instance)

        return serializer.to_representation(instance)


class FederatedObjectBaseSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        for attr_name, attr in attrs.items():
            if (
                isinstance(attr, serializers.Serializer) and
                not isinstance(
                    attr, (FederatedObjectBaseSerializer, )
                )
            ):
                raise TypeError(
                    f'Attribute {attr_name} should be a subclass of FederatedObjectSerializer'
                )

        type_iri = None
        if 'Meta' in attrs and hasattr(attrs['Meta'], 'model'):
            if 'id' not in attrs or not isinstance(attrs['id'], FederatedIdField):
                raise TypeError(f'{name} is missing an IdField')

            if 'type' not in attrs or not isinstance(attrs['type'], TypeField):
                raise TypeError(f'{name} is missing a TypeField')

            type_iri = expand_iri(attrs['type'].type)

            if expand_iri(attrs['type'].type).startswith('_:'):
                raise TypeError(f'{attrs["type"].type} is not a correct ActivityPub type')

        result = super().__new__(cls, name, bases, attrs)

        if type_iri:
            FederatedObjectSerializer.serializer_mapping[result.Meta.model] = result

        return result


class FederatedObjectBaseSerializer(
    serializers.ModelSerializer, metaclass=FederatedObjectBaseSerializerMetaclass
):
    def __init__(self, *args, origin=None, **kwargs):
        self.origin = origin
        super().__init__(*args, **kwargs)

    class Meta:
        fields = ('id', 'type')
        list_serializer_class = FederatedObjectListSerializer

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not self.parent:
            representation['@context'] = default_context

        if not representation['id']:
            representation.pop('id')

        return representation

    def create(self, validated_data):
        iri = validated_data.pop('id', None)
        validated_data['origin'] = ActivityPubModel.objects.from_iri(iri)

        for field in self.fields.values():
            if isinstance(field, (FederatedObjectSerializer, )):
                if (
                    field.source != '*' and
                    field.source in validated_data and
                    validated_data[field.source]
                ):
                    field.initial_data = validated_data[field.source]

                    validated_data[field.source] = field.create(validated_data[field.source])

        instance = super().create(validated_data)

        if self.origin:
            self.origin.federated_object = instance
            self.origin.save()

        return instance

    def update(self, instance, validated_data):
        validated_data.pop('id', None)

        for name, field in self.fields.items():
            if isinstance(field, (FederatedObjectSerializer, )):
                if validated_data.get(name, None):
                    field.initial_data = validated_data[name]
                    field.is_valid()
                    validated_data[field.source] = field.save()

        return super().update(instance, validated_data)
