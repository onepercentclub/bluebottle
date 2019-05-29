from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer, ActivitySubmitSerializer
)
from bluebottle.events.models import Event, Participant
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.transitions.serializers import TransitionSerializer


class EventSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('event-detail', view_args=('pk',))

    class Meta(BaseActivitySerializer.Meta):
        model = Event
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'end_time',
            'start_time',
            'location',
            'permissions',
            'registration_deadline',
        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'initiative',
            'place'
        ]
        resource_name = 'events'

    included_serializers = {
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'place': 'bluebottle.geo.serializers.GeolocationSerializer',
    }


class EventSubmitSerializer(ActivitySubmitSerializer):
    capacity = serializers.IntegerField(required=True)
    start = serializers.DateTimeField(required=True)
    end = serializers.DateTimeField(required=True)
    registration_deadline = serializers.DateTimeField(required=True)

    class Meta(ActivitySubmitSerializer.Meta):
        model = Event
        fields = ActivitySubmitSerializer.Meta.fields + (
            'capacity',
            'start',
            'end',
            'location',
            'registration_deadline',
        )


class EventTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Event.objects.all())
    field = 'status'
    included_serializers = {
        'resource': 'bluebottle.events.serializers.EventSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', ]
        resource_name = 'event-transitions'


class ParticipantSerializer(BaseContributionSerializer):
    included_serializers = {
        'activity': 'bluebottle.events.serializers.EventSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(BaseContributionSerializer.Meta):
        model = Participant
        fields = BaseContributionSerializer.Meta.fields + ('time_spent', )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'participants'
        included_resources = [
            'user',
            'activity'
        ]


class ParticipantTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Participant.objects.all())
    field = 'status'
    included_serializers = {
        'resource': 'bluebottle.events.serializers.ParticipantSerializer',
        'resource.activity': 'bluebottle.events.serializers.EventSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', 'resource.activity']
        resource_name = 'participant-transitions'
