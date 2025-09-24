from urllib.parse import urlparse

from django.urls import resolve
from django.db import models

from rest_framework import serializers, exceptions

from bluebottle.activity_pub.processor import default_context
from bluebottle.activity_pub.serializers.fields import IdField, TypeField
from bluebottle.activity_pub.utils import is_local
from bluebottle.activity_pub.adapters import adapter


class ActivityPubSerializer(serializers.ModelSerializer):
    type = TypeField()

    def __init__(self, *args, **kwargs):
        self.include = kwargs.pop('include', False)

        super().__init__(*args, **kwargs)

    class Meta:
        exclude = ('polymorphic_ctype', 'iri')

    def create(self, validated_data):
        for name, field in self.fields.items():
            if isinstance(field, ActivityPubSerializer):
                try:
                    iri = validated_data[name]['iri']
                    if not is_local(iri):
                        validated_data[name] = adapter.sync(iri, type(field))
                    else:
                        validated_data[name] = field.Meta.model.objects.get(
                            pk=resolve(urlparse(iri).path).kwargs['pk']
                        )
                except (KeyError, field.Meta.model.DoesNotExist):
                    field.initial_data = validated_data[name]
                    field.is_valid(raise_exception=True)
                    validated_data[name] = field.save(**validated_data[name])

        return self.Meta.model.objects.create(**validated_data)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        if self.parent:
            if not self.include:
                return result['id']
            else:
                del result['type']

                return result
        else:
            return result

    def to_internal_value(self, data):
        if isinstance(data, str):
            return {'iri': data} 

        result = super().to_internal_value(data)

        if 'id' in data and not is_local(data['id']):
            result['iri'] = data['id']

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self._serializers = [
            serializer(*args, **kwargs) for serializer in self.polymorphic_serializers
        ]

    def bind(self, field_name, parent):
        super().bind(field_name, parent)

        for serializer in self._serializers:
            serializer.bind(field_name, parent)

    def get_serializer(self, data):
        if isinstance(data, models.Model):
            for serializer in self._serializers:
                if serializer.Meta.model == data.__class__:
                    return serializer

            raise TypeError(f'Incompatible serializers for type: {type(data)}')
        else:
            if 'type' not in data:
                raise exceptions.ValidationError({'type': 'This field is required'})

            for serializer in self._serializers:
                if data['type'] == serializer.Meta.type:
                    return serializer

            raise exceptions.ValidationError(f'No serializer found for type: {data["type"]}')

    def to_representation(self, instance):
        return self.get_serializer(instance).to_representation(instance)

    def to_internal_value(self, data):
        return self.get_serializer(data).to_internal_value(data)

    def save(self, *args, **kwargs):
        self.instance = self.get_serializer(self.initial_data).save(*args, **kwargs)

        return self.instance

    def create(self, validated_data):
        return self.get_serializer(self.initial_data).create(validated_data)

    def update(self, instance, validated_data):
        return self.get_serializer(instance).update(validated_data)

    def is_valid(self, *args, **kwargs):
        model_classes = [serializer.Meta.model for serializer in self._serializers]

        if self.instance and type(self.instance) not in model_classes:
            raise TypeError(f'Incompatible serializers for type: {type(self.instance)}')

        serializer = self.get_serializer(self.initial_data)

        if serializer.is_valid(*args, **kwargs):
            self._validated_data = serializer.validated_data
            return True

        return False


class FederatedObjectSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', )

    def to_internal_value(self, data):
        pass

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['@context'] = default_context

        if not representation['id']:
            representation.pop('id')

        return representation
