import inflection
from rest_framework import serializers, relations

from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.processor import default_context, expand_iri
from bluebottle.activity_pub.serializers.fields import FederatedIdField, ActivityPubIdField, TypeField
from bluebottle.activity_pub.serializers import ActivityPubSerializer, FederatedObjectSerializer
from bluebottle.activity_pub.serializers.relations import RelatedResourceField, ManyResourceRelatedField
from bluebottle.activity_pub.utils import is_local


class ActivityPubSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        for attr_name, attr in attrs.items():
            if (
                isinstance(attr, serializers.Serializer) and
                not isinstance(attr, BaseActivityPubSerializer)
            ):
                raise TypeError(
                    f'Attribute {attr_name} should be a subclass of ActivityPubSerializer'
                )

        type_iri = None
        if 'Meta' in attrs and hasattr(attrs['Meta'], 'model'):
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


class BaseActivityPubSerializer(serializers.ModelSerializer, metaclass=ActivityPubSerializerMetaclass):
    id = ActivityPubIdField()

    def __init__(self, *args, full=True, include=False, origin=None, **kwargs):
        self.origin = origin
        self.include = include
        self.full = full

        super().__init__(*args, **kwargs)

    class Meta:
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
        many_related = {}

        if iri and not is_local(iri):
            instance = self.Meta.model.objects.filter(iri=iri).first()
            if instance:
                return self.update(instance, validated_data)

        for name, field in self.fields.items():
            if name in validated_data:
                if isinstance(field, ManyResourceRelatedField):
                    many_related[name] = field.save(validated_data.pop(name))
                if isinstance(field, RelatedResourceField):
                    validated_data[name] = field.save(validated_data[name])

        validated_data.pop('type', None)
        if self.origin:
            validated_data['origin'] = self.origin

        instance = self.Meta.model.objects.create(**validated_data)

        for field, related in many_related.items():
            getattr(instance, field).set(related)

        return instance

    def update(self, instance, validated_data):
        iri = validated_data.pop('iri', None)
        request = self.context.get('request')
        request_auth = getattr(request, 'auth', None)
        auth_iri = getattr(request_auth, 'iri', None)
        many_related = {}

        if (
            is_local(iri) and
            request_auth and
            auth_iri and
            not is_local(auth_iri)
        ):
            return instance

        for name, field in self.fields.items():
            if name in validated_data:
                if isinstance(field, relations.ManyRelatedField):
                    many_related[name] = [
                        field.child_relation.save(item) for item in validated_data.pop(name)
                    ]

                if isinstance(field, RelatedResourceField):
                    validated_data[name] = field.save(validated_data[name])

        validated_data.pop('type', None)
        instance = super().update(instance, validated_data)

        for field, related in many_related.items():
            getattr(instance, field).set(related)

        return instance

    def get_value(self, data):
        result = super().get_value(data)

        if isinstance(result, str):
            result = {'id': result}

        return result


class FederatedObjectBaseSerializerMetaclass(serializers.SerializerMetaclass):
    def __new__(cls, name, bases, attrs):
        for attr_name, attr in attrs.items():
            if (
                isinstance(attr, serializers.Serializer) and
                not isinstance(
                    attr, (FederatedObjectBaseSerializer, FederatedObjectSerializer)
                )
            ):
                raise TypeError(
                    f'Attribute {attr_name} should be a subclass of FederatedObjectSerializer'
                )

        type_iri = None
        if 'Meta' in attrs and hasattr(attrs['Meta'], 'model'):
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
    id = FederatedIdField()

    class Meta:
        fields = ('id', 'type')

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if not self.parent:
            representation['@context'] = default_context

        if not representation['id']:
            representation.pop('id')

        return representation

    def to_internal_value(self, data):
        if isinstance(data, str):
            instance = ActivityPubModel.objects.from_iri(data)
            data = ActivityPubSerializer(instance=instance).data

        return super().to_internal_value(data)

    def create(self, validated_data):
        iri = validated_data.pop('id', None)

        for field in self.fields.values():
            if isinstance(field, (FederatedObjectSerializer, FederatedObjectBaseSerializer)):
                if (
                    field.source != '*' and
                    field.source in validated_data and
                    validated_data[field.source]
                ):
                    field_data = validated_data[field.source]
                    if is_local(field_data['id']):
                        validated_data[field.source] = ActivityPubModel.objects.from_iri(
                            field_data['id']
                        ).origin
                    else:
                        field.initial_data = field_data

                        validated_data[field.source] = field.create(field_data)

        result = super().create(validated_data)
        origin = ActivityPubModel.objects.from_iri(iri)
        if origin:
            origin.adopted = result
            origin.save()

        return result

    def update(self, instance, validated_data):
        validated_data.pop('id', None)

        for name, field in self.fields.items():
            if isinstance(field, (FederatedObjectSerializer, FederatedObjectBaseSerializer)):
                if validated_data.get(field.source, None):
                    field.initial_data = self.initial_data[name]
                    field.instance = getattr(instance, field.source, None)
                    field.is_valid(raise_exception=True)
                    validated_data[field.source] = field.save()

        return super().update(instance, validated_data)
