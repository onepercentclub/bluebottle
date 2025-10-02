from urllib.parse import urlparse

from django.urls import resolve

from rest_framework import serializers, exceptions

from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.processor import default_context
from bluebottle.activity_pub.utils import is_local
from bluebottle.activity_pub.adapters import adapter


class ActivityPubSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        self.include = kwargs.pop('include', False)

        super().__init__(*args, **kwargs)

    class Meta:
        fields = ('type', 'id')

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not self.parent:
            return representation
        else:
            if self.include:
                representation.pop('type', None)
                return representation
            else:
                return representation['id']

    def to_internal_value(self, data):
        try:
            return super().to_internal_value(data)
        except exceptions.ValidationError:
            if tuple(data.keys()) == ('id', ):
                iri = data['id']
                if not is_local(iri):
                    try:
                        instance = self.Meta.model.objects.get(iri=iri)
                        return type(self)(instance=instance).data
                    except self.Meta.model.DoesNotExist:
                        data = adapter.fetch(iri)
                        return super().to_internal_value(data)
                else:
                    resolved = resolve(urlparse(iri).path)
                    instance = self.Meta.model.objects.get(pk=resolved.kwargs['pk'])
                    return type(self)(instance=instance).data
            else:
                raise

    def save(self, **kwargs):
        iri = self.validated_data.get('id', None)

        if iri:
            model_class = self.Meta.model
            try:
                if not is_local(iri):
                    self.instance = model_class.objects.get(iri=iri)
                else:
                    resolved = resolve(urlparse(iri).path)
                    self.instance = self.Meta.model.objects.get(pk=resolved.kwargs['pk'])
            except self.Meta.model.DoesNotExist:
                pass

        return super().save(**kwargs)

    def create(self, validated_data):
        iri = validated_data.pop('id', None)
        if iri and not is_local(iri):
            validated_data['iri'] = iri

        for name, field in self.fields.items():
            if isinstance(field, (ActivityPubSerializer, PolymorphicActivityPubSerializer)):
                field.initial_data = validated_data.get(name, None)
                field.is_valid(raise_exception=True)
                if validated_data.get(name, None):
                    validated_data[name] = field.save()

        validated_data.pop('type', None)
        return self.Meta.model.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('id', None)

        for name, field in self.fields.items():
            if isinstance(field, (ActivityPubSerializer, PolymorphicActivityPubSerializer)):
                field.initial_data = validated_data[name]
                field.is_valid()
                validated_data[name] = field.save()

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._serializers = [
            serializer(*args, **kwargs) for serializer in self.polymorphic_serializers
        ]

    def get_serializer_from_model(self, model):
        for serializer in self._serializers:
            if serializer.Meta.model == model:
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
            if tuple(data.keys()) == ('id', ):
                iri = data['id']
                if not is_local(iri):
                    try:
                        instance = self.Meta.model.objects.get(iri=iri)
                        return type(self)(instance=instance).data
                    except self.Meta.model.DoesNotExist:
                        data = adapter.fetch(iri)
                        return self.get_serializer_from_data(data).to_internal_value(data)
                else:
                    resolved = resolve(urlparse(iri).path)
                    instance = self.Meta.model.objects.get(pk=resolved.kwargs['pk'])
                    return type(self)(instance=instance).data
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


class FederatedObjectSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', )

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not self.parent:
            representation['@context'] = default_context

        if not representation['id']:
            representation.pop('id')

        return representation

    def create(self, validated_data):
        iri = validated_data.pop('id')
        validated_data['origin'] = ActivityPubModel.objects.get(iri=iri)

        for field in self.fields.values():
            if isinstance(field, (FederatedObjectSerializer)):
                if field.source != '*':
                    field.initial_data = validated_data[field.source]

                    validated_data[field.source] = field.create(validated_data[field.source])

        return super().create(validated_data)
