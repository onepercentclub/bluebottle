from django.db import models
from rest_framework.relations import RelatedField, ManyRelatedField
from rest_framework.exceptions import ValidationError

from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.serializers import ActivityPubSerializer, FederatedObjectSerializer
from bluebottle.activity_pub.clients import client
from bluebottle.activity_pub.utils import is_local


class ManyResourceRelatedField(ManyRelatedField):
    def to_internal_value(self, data):
        if not isinstance(data, (tuple, list)):
            # In json-ld list are compacted to single items. Make a list again in that case
            data = [data]

        return super().to_internal_value(data)

    def get_related_origin(self):
        origin = self.parent.origin
        if not origin:
            return []

        serializer = FederatedObjectSerializer()._get_serializer_from_model_or_instance(
            origin
        )
        field = serializer.fields.get(self.source)
        if field is None:
            return []

        related = getattr(origin, field.source)
        return related.all()

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

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = {'id': data}

        if 'type' not in data and isinstance(self.type, str):
            data = dict(type=self.type, **data)

        serializer = ActivityPubSerializer(context=self.context)

        try:
            return serializer.to_internal_value(data)
        except ValidationError as e:
            if 'id' in data:
                instance = ActivityPubModel.objects.from_iri(data['id'])

                if instance:
                    local_data = ActivityPubSerializer(instance=instance, context=self.context).data
                    return serializer.to_internal_value(local_data)
                elif not is_local(data['id']):
                    fetched_data = client.fetch(data['id'])
                    return serializer.to_internal_value(fetched_data)
            else:
                raise e

    def get_related_origin(self):
        try:
            origin = self.parent.origin
            if not origin:
                return None

            serializer = FederatedObjectSerializer(context=self.context)._get_serializer_from_model_or_instance(
                origin
            )
            field = serializer.fields.get(self.source)
            if field is None:
                return None

            if hasattr(field, 'get_origin_value'):
                related_origin = field.get_origin_value(origin)
            else:
                related_origin = getattr(origin, field.source)

            if isinstance(related_origin, models.Model):
                return related_origin
        except AttributeError:
            pass

    def save(self, value, origin=None):
        if value is not None:
            serializer = ActivityPubSerializer(
                data=value,
                origin=origin or self.get_related_origin(),
                context=self.context
            )

            if 'iri' in value:
                model_class = serializer.resource_type_model_mapping[value['type']]
                serializer.instance = model_class.objects.from_iri(value['iri'])

            serializer._validated_data = value
            serializer._errors = []
            return serializer.save()
