from django.db.models import Model
from rest_framework import serializers
from rest_framework_json_api.relations import PolymorphicResourceRelatedField
from rest_framework_json_api.serializers import (
    PolymorphicModelSerializer
)

from bluebottle.events.models import Event
from bluebottle.funding.serializers import DonorSerializer, FundingSerializer


class EventObjectSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DonorSerializer,
        FundingSerializer,
    ]

    class Meta(object):
        model = Model

    class JSONAPIMeta(object):
        resource_name = 'events/objects'


class EventSerializer(serializers.ModelSerializer):

    content_object = PolymorphicResourceRelatedField(
        polymorphic_serializer=EventObjectSerializer,
        read_only=True,
    )

    class Meta:
        model = Event
        fields = ('id', 'created', 'updated', 'content_object')

    class JSONAPIMeta:
        included_resources = [
            'content_object',
        ]
        resource_name = 'events'

    included_serializers = {
        'content_object': 'bluebottle.events.serializers.EventObjectSerializer',
    }
