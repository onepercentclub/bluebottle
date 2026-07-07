from django.db import models
from rest_framework.relations import RelatedField, ManyRelatedField
from rest_framework.exceptions import ValidationError

from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.serializers import ActivityPubSerializer, FederatedObjectSerializer
from bluebottle.activity_pub.clients import client
from bluebottle.activity_pub.utils import (
    find_activity_pub_instance,
    get_local_resource_data,
    is_local,
    resource_type_from_url,
)


def enrich_resource_value(value):
    if not isinstance(value, dict):
        return value

    if value.get('url'):
        return value

    resource_iri = value.get('iri') or value.get('id')
    if not resource_iri:
        return value

    instance = ActivityPubModel.objects.from_iri(resource_iri)
    if instance and getattr(instance, 'url', None):
        return {**value, 'url': instance.url}

    local_data = get_local_resource_data(resource_iri)
    if isinstance(local_data, dict) and local_data.get('url'):
        return {**value, 'url': local_data['url']}

    if not is_local(resource_iri):
        fetched = client.fetch(resource_iri)
        if isinstance(fetched, dict) and fetched.get('url'):
            return {**value, 'url': fetched['url']}

    return value


class ManyResourceRelatedField(ManyRelatedField):
    def to_internal_value(self, data):
        if not isinstance(data, (tuple, list)):
            # In json-ld list are compacted to single items. Make a list again in that case
            data = [data]

        return super().to_internal_value(data)

    def get_related_origin(self):
        origin = self.parent.origin
        if origin and getattr(origin, 'iri', None):
            return []

        if origin:
            serializer = FederatedObjectSerializer()._get_serializer_from_model_or_instance(
                origin
            )
            source = serializer.fields[self.source].source
            return getattr(origin, source).all()
        else:
            return []

    def save(self, validated_data):
        related_origin = self.get_related_origin()

        return [
            self.child_relation.save(
                item, origin=related_origin[index] if index < len(related_origin) else None
            ) for index, item in enumerate(validated_data)
        ]


class RelatedResourceField(RelatedField):
    def __init__(self, type, include=False, *args, **kwargs):
        self.include = include
        self.type = type
        super().__init__(*args, **kwargs)

    @classmethod
    def many_init(cls, type, include, *args, **kwargs):
        kwargs['child_relation'] = cls(type, include)
        return ManyResourceRelatedField(*args, **kwargs)

    def get_queryset(self):
        # TODO: filter queryset on correct types
        return ActivityPubModel.objects.all()

    def to_representation(self, value):
        return ActivityPubSerializer(
            full=False, include=self.include
        ).to_representation(value)

    def _ensure_type(self, data):
        if 'type' in data or 'id' not in data:
            return data

        if isinstance(self.type, str):
            return dict(type=self.type, **data)

        if isinstance(self.type, (tuple, list)):
            resource_type = resource_type_from_url(data['id'], self.type)
            if resource_type:
                return dict(type=resource_type, **data)

        return data

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = {'id': data}

        data = self._ensure_type(data)

        serializer = ActivityPubSerializer()

        try:
            return serializer.to_internal_value(data)
        except ValidationError as e:
            if 'id' not in data:
                raise e

            instance = ActivityPubModel.objects.from_iri(data['id'])

            if instance:
                local_data = ActivityPubSerializer(instance=instance).data
                return serializer.to_internal_value(local_data)

            local_data = get_local_resource_data(data['id'])
            if local_data:
                return serializer.to_internal_value(local_data)

            if not is_local(data['id']):
                fetched_data = client.fetch(data['id'])
                return serializer.to_internal_value(fetched_data)

            raise e

    def _parent_is_remote(self, data=None):
        parent_instance = getattr(self.parent, 'instance', None)
        if parent_instance and getattr(parent_instance, 'iri', None):
            return True

        for source in (
            getattr(self.parent, '_validated_data', None),
            getattr(self.parent, 'initial_data', None),
        ):
            if isinstance(source, dict) and (source.get('iri') or source.get('id')):
                return True

        return False

    def get_related_origin(self, value=None):
        try:
            if self._parent_is_remote(value):
                return None

            origin = self.parent.origin
            if origin:
                serializer = FederatedObjectSerializer()._get_serializer_from_model_or_instance(
                    origin
                )
                source = serializer.fields[self.source].source
                related_origin = getattr(origin, source)

                if isinstance(related_origin, models.Model):
                    return related_origin
            else:
                return None
        except AttributeError:
            pass

    def save(self, value, origin=None):
        if value is not None:
            value = enrich_resource_value(value)

            resource_iri = value.get('iri') or value.get('id')
            instance = find_activity_pub_instance(resource_iri) if resource_iri else None

            serializer = ActivityPubSerializer(
                instance=instance,
                origin=origin or self.get_related_origin(value)
            )

            serializer._validated_data = value
            serializer._errors = []
            return serializer.save()
