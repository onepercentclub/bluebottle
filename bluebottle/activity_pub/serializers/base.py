from django.db import models
from rest_framework import serializers, exceptions

from bluebottle.activity_pub.serializers.fields import IdField, TypeField
from bluebottle.activity_pub.utils import is_local


class ActivityPubSerializer(serializers.ModelSerializer):
    type = TypeField()
    id = IdField(source="*", required=False)

    class Meta:
        exclude = ('polymorphic_ctype', 'url')

    def get_url_name(self, instance):
        return self.Meta.url_name

    def to_internal_value(self, data):
        result = super().to_internal_value(data)

        if 'id' in data and not is_local(data['id']):
            result['url'] = data['id']

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
        self._serializers = [
            serializer(*args, **kwargs) for serializer in self.polymorphic_serializers
        ]
        super().__init__(*args, **kwargs)

    def get_url_name(self, instance):
        return self.get_serializer(instance).Meta.url_name

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
        return self.get_serializer(self.initial_data).save(*args, **kwargs)

    def create(self, validated_data):
        return self.get_serializer(self.initial_data).create(validated_data)

    def update(self, instance, validated_data):
        return self.get_serializer(instance).update(validated_data)

    def is_valid(self, *args, **kwargs):
        super().is_valid(*args, **kwargs)

        model_classes = [serializer.Meta.model for serializer in self._serializers]

        if self.instance and type(self.instance) not in model_classes:
            raise TypeError(f'Incompatible serializers for type: {type(self.instance)}')

        serializer = self.get_serializer(self.initial_data)

        return serializer.is_valid(*args, **kwargs)


class FederatedObjectSerializer(serializers.ModelSerializer):
    type = TypeField()
    id = IdField(source="*", required=False)

    def to_internal_value(self, data):
        pass
