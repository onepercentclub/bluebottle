from rest_framework.relations import RelatedField
from rest_framework.exceptions import ValidationError

from bluebottle.activity_pub.models import ActivityPubModel
from bluebottle.activity_pub.serializers.base import ActivityPubSerializer
from bluebottle.activity_pub.clients import client
from bluebottle.activity_pub.utils import is_local


class RelatedResourceField(RelatedField):
    def __init__(self, type, include=False, *args, **kwargs):
        self.include = include
        self.type = type
        super().__init__(*args, **kwargs)

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
            try:
                data = dict(type=self.type, **data)
            except:
                __import__('ipdb').set_trace()

        serializer = ActivityPubSerializer()

        try:
            internal_value = serializer.to_internal_value(data)
        except ValidationError as e:
            if 'id' in data:
                if is_local(data['id']):
                    instance = ActivityPubModel.objects.from_iri(data['id'])
                    local_data = ActivityPubSerializer(instance=instance).data
                    return serializer.to_internal_value(local_data)
                else:
                    fetched_data = client.fetch(data['id'])
                    internal_value = serializer.to_internal_value(fetched_data)
            else:
                return {'id': None}

        return internal_value

    def save(self, value):
        if value is not None:
            serializer = ActivityPubSerializer(data=value)

            if 'iri' in value:
                model_class = serializer.resource_type_model_mapping[value['type']]
                serializer.instance = model_class.objects.from_iri(value['iri'])

            serializer._validated_data = value
            serializer._errors = []

            return serializer.save()
