from django.db.models import Model
from rest_framework import serializers
from rest_framework_json_api.relations import PolymorphicResourceRelatedField
from rest_framework_json_api.serializers import (
    PolymorphicModelSerializer
)

from bluebottle.events.models import Event
from bluebottle.funding.serializers import DonorSerializer, FundingSerializer
from bluebottle.deeds.serializers import (
    DeedParticipantSerializer, DeedSerializer
)


class EventObjectSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DonorSerializer,
        FundingSerializer,
        DeedParticipantSerializer,
        DeedSerializer,
    ]

    class Meta(object):
        model = Model
        fields = ('activity',)
        meta_fields = (
            'permissions',
            'transitions',
            'created',
            'updated',
            'errors',
            'required',
            'matching_properties',
            'deleted_successful_contributors',
            'contributor_count',
            'team_count',
            'current_status',
            'admin_url',
        )

    class JSONAPIMeta(object):
        resource_name = 'events/objects'

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }


class EventSerializer(serializers.ModelSerializer):

    content_object = PolymorphicResourceRelatedField(
        polymorphic_serializer=EventObjectSerializer,
        read_only=True,
    )

    class Meta:
        model = Event
        fields = ('id', 'created', 'updated', 'content_object', 'event_type')
        meta_fields = ('created', 'updated')

    class JSONAPIMeta:
        included_resources = [
            'content_object',
            'content_object.activity',
        ]
        resource_name = 'events'

    included_serializers = {
        'content_object': 'bluebottle.events.serializers.EventObjectSerializer',
        'content_object.activity': 'bluebottle.activities.serializers.ActivitySerializer',
    }
