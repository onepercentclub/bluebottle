from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer, ActivitySubmitSerializer
)
from bluebottle.events.models import Event, Participant
from bluebottle.geo.models import Geolocation
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
            'is_online',
            'location',
            'location_hint',
            'permissions',
            'registration_deadline',
        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'initiative',
            'initiative.image',
            'location',
            'contributions'
        ]
        resource_name = 'activities/events'

    included_serializers = {
        'contributions': 'bluebottle.events.serializers.ParticipantSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
    }


class EventSubmitSerializer(ActivitySubmitSerializer):
    start_time = serializers.DateTimeField(
        required=True,
        error_messages={
            'blank': _('Start time is required'),
            'null': _('Start time is required')
        }
    )
    end_time = serializers.DateTimeField(
        required=True,
        error_messages={
            'blank': _('End time is required'),
            'null': _('End time is required')
        }
    )

    location = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        allow_empty=True,
        queryset=Geolocation.objects.all(),
        error_messages={
            'blank': _('Location is required'),
            'null': _('Location is required')
        }
    )

    def validate(self, data):
        """
        Check that location is set if not online
        """
        if not self.initial_data['is_online'] and not data['location']:
            raise serializers.ValidationError("Location is required or select 'is online'")
        return data

    class Meta(ActivitySubmitSerializer.Meta):
        model = Event
        fields = ActivitySubmitSerializer.Meta.fields + (
            'start_time',
            'end_time',
            'location',
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

        validators = [
            UniqueTogetherValidator(
                queryset=Participant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/participants'
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
