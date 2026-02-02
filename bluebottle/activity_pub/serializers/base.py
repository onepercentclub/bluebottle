from urllib.parse import urlparse

from django.db import connection
from django.urls import resolve
import inflection
from rest_framework import serializers, exceptions

from bluebottle.activity_pub.adapters import adapter
from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.processor import default_context, expand_iri
from bluebottle.activity_pub.serializers.fields import FederatedIdField, ActivityPubIdField, TypeField
from bluebottle.activity_pub.utils import is_local


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


class ActivityPubSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        for attr_name, attr in attrs.items():
            if (
                isinstance(attr, serializers.Serializer) and
                not isinstance(
                    attr,
                    (ActivityPubSerializer, ActivityPubListSerializer, PolymorphicActivityPubSerializer)
                )
            ):
                raise TypeError(
                    f'Attribute {attr_name} should be a subclass of ActivityPubSerializer'
                )

        if 'Meta' in attrs and hasattr(attrs['Meta'], 'model'):
            if 'id' not in attrs or not isinstance(attrs['id'], ActivityPubIdField):
                raise TypeError(f'{name} is missing an IdField')

            if 'type' not in attrs or not isinstance(attrs['type'], TypeField):
                raise TypeError(f'{name} is missing a TypeField')

            if expand_iri(attrs['type'].type).startswith('_:'):
                raise TypeError(f'{attrs["type"].type} is not a correct ActivityPub type')

            for [attr, field] in attrs.items():
                if (
                    isinstance(field, (ActivityPubSerializer, serializers.Field)) and
                    attr not in ('id', 'type', )
                ):
                    if expand_iri(inflection.camelize(attr, False)).startswith('_:'):
                        raise TypeError(
                            f'{attr} is not a correct ActivityPub type'
                        )

        return super().__new__(cls, name, bases, attrs)


class ActivityPubSerializer(serializers.ModelSerializer, metaclass=ActivityPubSerializerMetaclass):
    def __init__(self, *args, full=False, include=False, **kwargs):
        self.include = include

        super().__init__(*args, **kwargs)

        self.context['full'] = full

    class Meta:
        list_serializer_class = ActivityPubListSerializer
        fields = ('type', 'id')

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not self.parent:
            return representation
        else:
            if self.include or self.context['full']:
                representation.pop('type', None)
                return representation
            else:
                return representation['id']

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except exceptions.ValidationError:
            if not isinstance(data, (dict, str)) and 'url' in self.fields:
                url = getattr(data, 'url', None)
                if not url and hasattr(data, 'file'):
                    url = getattr(data.file, 'url', None)
                if url:
                    if isinstance(url, str) and url.startswith('/'):
                        url = connection.tenant.build_absolute_url(url)
                    name = getattr(data, 'name', None)
                    if not name and hasattr(data, 'file'):
                        name = getattr(data.file, 'name', None)
                    return super().to_internal_value({'url': url, 'name': name})
            if isinstance(data, str):
                data = {'id': data}

            if tuple(data.keys()) == ('id',):
                iri = data['id']
                instance = self.Meta.model.objects.from_iri(iri)

                if instance:
                    return type(self)(instance=instance).data
                elif not is_local(iri):
                    data = adapter.fetch(iri)
                    return super().to_internal_value(data)

            else:
                raise

    def save(self, **kwargs):
        iri = self.validated_data.get('id', None)

        if iri:
            self.instance = self.Meta.model.objects.from_iri(iri)

        return super().save(**kwargs)

    def create(self, validated_data):
        iri = validated_data.pop('id', None)
        if iri and not is_local(iri):
            validated_data['iri'] = iri
            instance = self.Meta.model.objects.filter(iri=iri).first()
            if instance:
                return self.update(instance, validated_data)

        for name, field in self.fields.items():
            if (
                isinstance(field, (ActivityPubSerializer, PolymorphicActivityPubSerializer)) and
                not getattr(field, 'many', False)
            ):
                if validated_data.get(name, None):
                    field.initial_data = validated_data.get(name, None)
                    field.is_valid(raise_exception=True)
                    validated_data[field.source] = field.save()

        validated_data.pop('type', None)
        return self.Meta.model.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('id', None)

        for name, field in self.fields.items():
            if isinstance(
                field,
                (ActivityPubSerializer, ActivityPubListSerializer, PolymorphicActivityPubSerializer)
            ):
                if validated_data.get(name, None):
                    field.initial_data = validated_data[name]
                    field.is_valid()
                    validated_data[field.source] = field.save()

        validated_data.pop('type', None)
        return super().update(instance, validated_data)

    def get_value(self, data):
        result = super().get_value(data)

        if isinstance(result, str):
            result = {'id': result}

        return result


class PolymorphicActivityPubSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, *args, **kwargs):
        result = super().__new__(cls, *args, **kwargs)
        if hasattr(result, 'polymorphic_serializers'):
            for serializer in result.polymorphic_serializers:
                if not issubclass(serializer.Meta.model, result.Meta.model):
                    raise TypeError(f'{serializer.Meta.model} is not a subclass of {result.Meta.model}')

        return result


class PolymorphicActivityPubSerializer(
    serializers.Serializer, metaclass=PolymorphicActivityPubSerializerMetaclass
):
    def __init__(self, *args, full=False, **kwargs):
        full = full
        super().__init__(*args, **kwargs)

        self._serializers = [
            serializer(*args, full=full, **kwargs) for serializer in self.polymorphic_serializers
        ]

    def get_serializer_from_model(self, model):
        for serializer in self._serializers:
            if issubclass(model, serializer.Meta.model):
                return serializer

        raise TypeError(f'Missing serializer for model: {model}')

    def get_serializer_from_data(self, data):
        if 'id' in data and 'type' not in data:
            iri = data['id']

            if is_local(iri):
                resolved = resolve(urlparse(iri).path)
                return self.get_serializer_from_model(resolved.func.view_class.queryset.model)

        if 'type' not in data:
            raise exceptions.ValidationError({'type': 'Missing type information'})

        for serializer in self._serializers:
            if data['type'] == serializer.fields['type'].type:
                return serializer

        raise exceptions.ValidationError(f'Missing serializer for type: {data["type"]}')

    def bind(self, field_name, parent):
        super().bind(field_name, parent)

        for serializer in self._serializers:
            serializer.bind(field_name, parent)

    def to_representation(self, instance):
        return self.get_serializer_from_model(type(instance)).to_representation(instance)

    def to_internal_value(self, data):
        try:
            return self.get_serializer_from_data(data).to_internal_value(data)
        except exceptions.ValidationError:
            if isinstance(data, str):
                data = {'id': data}

            if tuple(data.keys()) == ('id', ):
                iri = data['id']
                instance = self.Meta.model.objects.from_iri(iri)
                if instance:
                    return type(self)(instance=instance).data
                elif not is_local(iri):
                    data = adapter.fetch(iri)
                    return self.get_serializer_from_data(data).to_internal_value(data)
            else:
                raise

    def get_value(self, data):
        result = super().get_value(data)

        if isinstance(result, str):
            result = {'id': result}

        return result

    def save(self, *args, **kwargs):
        self.instance = self.get_serializer_from_data(self.initial_data).save(*args, **kwargs)

        return self.instance

    def create(self, validated_data):
        return self.get_serialize_from_datar(self.initial_data).create(validated_data)

    def update(self, instance, validated_data):
        return self.get_serialize_from_datar(instance).update(validated_data)

    def is_valid(self, *args, **kwargs):
        model_classes = [serializer.Meta.model for serializer in self._serializers]

        if self.instance and type(self.instance) not in model_classes:
            raise TypeError(f'Incompatible serializers for type: {type(self.instance)}')

        serializer = self.get_serializer_from_data(self.initial_data)
        serializer.initial_data = self.initial_data

        if serializer.is_valid(*args, **kwargs):
            self._validated_data = serializer.validated_data
            return True

        return False


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


class FederatedObjectSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        for attr_name, attr in attrs.items():
            if (
                isinstance(attr, serializers.Serializer) and
                not isinstance(
                    attr, (FederatedObjectSerializer, )
                )
            ):
                raise TypeError(
                    f'Attribute {attr_name} should be a subclass of FederatedObjectSerializer'
                )

        if 'Meta' in attrs and hasattr(attrs['Meta'], 'model'):
            if 'id' not in attrs or not isinstance(attrs['id'], FederatedIdField):
                raise TypeError(f'{name} is missing an IdField')

        return super().__new__(cls, name, bases, attrs)


class FederatedObjectSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', )
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

        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('id', None)

        for name, field in self.fields.items():
            if isinstance(field, (FederatedObjectSerializer, )):
                if validated_data.get(name, None):
                    field.initial_data = validated_data[name]
                    field.is_valid()
                    validated_data[field.source] = field.save()

        return super().update(instance, validated_data)
