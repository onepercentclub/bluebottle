import inflection
from django.db import IntegrityError
from rest_framework import serializers, relations

from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.processor import default_context, expand_iri
from bluebottle.activity_pub.serializers.fields import FederatedIdField, ActivityPubIdField, TypeField
from bluebottle.activity_pub.serializers import ActivityPubSerializer, FederatedObjectSerializer
from bluebottle.activity_pub.serializers.relations import RelatedResourceField, ManyResourceRelatedField
from bluebottle.activity_pub.utils import (
    find_activity_pub_instance,
    get_local_resource_data,
    is_local,
    link_activity_pub_adopted,
    normalize_resource_url,
)


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
        iri = self.validated_data.get('iri') or self.validated_data.get('id')

        if iri and not self.instance:
            instance = find_activity_pub_instance(iri)
            if instance:
                self.instance = instance

        return super().save(**kwargs)

    def _is_remote_resource(self, instance=None, validated_data=None):
        if instance and getattr(instance, 'iri', None):
            return True
        if validated_data:
            resource_iri = validated_data.get('iri') or validated_data.get('id')
            if resource_iri and not is_local(resource_iri):
                return True
        return False

    def _clear_invalid_origin(self, instance):
        if not hasattr(instance, 'origin_id') or not instance.origin_id:
            return

        field = instance._meta.get_field('origin')
        if not field.related_model.objects.filter(pk=instance.origin_id).exists():
            instance.origin_id = None

    def _maybe_set_origin(self, validated_data, instance=None):
        if not self.origin or not hasattr(self.Meta.model, 'origin'):
            return

        if self._is_remote_resource(instance=instance, validated_data=validated_data):
            return

        field = self.Meta.model._meta.get_field('origin')
        if not field.related_model.objects.filter(pk=self.origin.pk).exists():
            return

        validated_data['origin'] = self.origin

    def _instance_for_iri(self, iri):
        return find_activity_pub_instance(iri)

    def _sanitize_create_data(self, validated_data, iri):
        validated_data.pop('type', None)
        validated_data.pop('id', None)
        validated_data.pop('pk', None)

        if iri:
            validated_data['iri'] = normalize_resource_url(iri)

        return validated_data

    def create(self, validated_data):
        iri = validated_data.get('iri') or validated_data.get('id')
        many_related = {}

        instance = self._instance_for_iri(iri)
        if instance:
            return self.update(instance, validated_data)

        for name, field in self.fields.items():
            if name in validated_data:
                if isinstance(field, ManyResourceRelatedField):
                    many_related[name] = field.save(validated_data.pop(name))
                if isinstance(field, RelatedResourceField):
                    validated_data[name] = field.save(validated_data[name])

        self._maybe_set_origin(validated_data)
        self._sanitize_create_data(validated_data, iri)

        try:
            if iri:
                instance, _ = self.Meta.model.objects.update_or_create(
                    iri=validated_data['iri'],
                    defaults=validated_data,
                )
            else:
                instance = self.Meta.model.objects.create(**validated_data)
        except IntegrityError:
            instance = self._instance_for_iri(iri)
            if instance:
                return self.update(instance, validated_data)
            raise

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
        if self._is_remote_resource(instance=instance, validated_data=validated_data):
            validated_data.pop('origin', None)
        self._clear_invalid_origin(instance)
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

    def _nested_field_data(self, name, field, validated_data):
        field_data = validated_data.get(field.source)
        if field_data is None and isinstance(self.initial_data, dict):
            field_data = self.initial_data.get(name)
        return field_data

    def _nested_field_has_substance(self, field_data):
        if not isinstance(field_data, dict):
            return bool(field_data)

        return bool(set(field_data.keys()) - {'id', 'iri', 'type', '@context'})

    def _enrich_nested_field_data(self, field_data):
        from bluebottle.activity_pub.clients import client

        if not isinstance(field_data, dict):
            return field_data

        if self._nested_field_has_substance(field_data):
            return field_data

        resource_iri = field_data.get('id') or field_data.get('iri')
        if not resource_iri:
            return field_data

        activity_pub_instance = ActivityPubModel.objects.from_iri(resource_iri)
        if activity_pub_instance:
            return ActivityPubSerializer(instance=activity_pub_instance).data

        local_data = get_local_resource_data(resource_iri)
        if local_data:
            return local_data

        if not is_local(resource_iri):
            fetched = client.fetch(resource_iri)
            if isinstance(fetched, dict):
                return fetched

        return field_data

    def _process_nested_field(self, field, name, field_data, instance=None):
        from bluebottle.activity_pub.serializers.federated_activities import ImageSerializer

        if not field_data:
            return getattr(instance, field.source, None) if instance else None

        field_data = self._enrich_nested_field_data(field_data)

        activity_pub_instance = ActivityPubModel.objects.from_iri(field_data.get('id'))
        if (
            instance is None and
            activity_pub_instance and
            is_local(field_data.get('id'))
        ):
            local_origin = getattr(activity_pub_instance, 'origin', None)
            if local_origin:
                return local_origin

            adopted_file = getattr(activity_pub_instance, 'adopted', None)
            if adopted_file and adopted_file.file:
                return adopted_file

        existing = getattr(instance, field.source, None) if instance else None
        if (
            instance is not None and
            not isinstance(field, ImageSerializer) and
            not self._nested_field_has_substance(field_data) and
            existing
        ):
            return existing

        field.initial_data = field_data
        field.instance = existing

        if isinstance(field, ImageSerializer) or instance is not None:
            field.is_valid(raise_exception=True)
            return field.save()

        return field.create(field_data)

    def create(self, validated_data):
        iri = validated_data.pop('id', None)

        for name, field in self.fields.items():
            if isinstance(field, (FederatedObjectSerializer, FederatedObjectBaseSerializer)):
                field_data = self._nested_field_data(name, field, validated_data)
                if field_data:
                    validated_data[field.source] = self._process_nested_field(
                        field, name, field_data
                    )

        result = super().create(validated_data)
        if iri:
            link_activity_pub_adopted(iri, result)

        return result

    def update(self, instance, validated_data):
        validated_data.pop('id', None)

        for name, field in self.fields.items():
            if isinstance(field, (FederatedObjectSerializer, FederatedObjectBaseSerializer)):
                field_data = self._nested_field_data(name, field, validated_data)
                if field_data:
                    validated_data[field.source] = self._process_nested_field(
                        field, name, field_data, instance=instance
                    )

        return super().update(instance, validated_data)
