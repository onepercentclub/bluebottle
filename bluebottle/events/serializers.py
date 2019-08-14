from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer, ActivitySubmitSerializer,
    ActivityValidationSerializer
)
from bluebottle.events.filters import ParticipantListFilter
from bluebottle.events.models import Event, Participant
from bluebottle.geo.models import Geolocation
from bluebottle.transitions.serializers import TransitionSerializer
from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField
from bluebottle.utils.serializers import (
    RelatedField, NonModelRelatedResourceField, NoCommitMixin
)


class ParticipantSerializer(BaseContributionSerializer):

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

    included_serializers = {
        'activity': 'bluebottle.events.serializers.EventSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class ParticipantTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Participant.objects.all())
    field = 'status'
    included_serializers = {
        'resource': 'bluebottle.events.serializers.ParticipantSerializer',
        'resource.activity': 'bluebottle.events.serializers.EventSerializer',
    }

    class JSONAPIMeta:
        resource_name = 'contributions/participant-transitions'
        included_resources = [
            'resource',
            'resource.activity'
        ]


class EventValidationSerializer(ActivityValidationSerializer):
    start_date = serializers.DateField()
    start_time = serializers.TimeField()
    duration = serializers.FloatField()
    is_online = serializers.BooleanField()
    location = RelatedField(queryset=Geolocation.objects.all())

    class Meta:
        model = Event
        fields = ActivityValidationSerializer.Meta.fields + (
            'start_date', 'start_time', 'is_online', 'location', 'duration'
        )

    class JSONAPIMeta:
        resource_name = 'activities/event-validations'


class EventListSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('event-detail', view_args=('pk',))
    validations = NonModelRelatedResourceField(EventValidationSerializer)

    class Meta(BaseActivitySerializer.Meta):
        model = Event
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'start_date',
            'start_time',
            'duration',
            'is_online',
            'location',
            'location_hint',
            'permissions',
            'registration_deadline',
            'validations',
        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'initiative',
            'initiative.image',
            'location',
            'validations',
        ]
        resource_name = 'activities/events'

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'validations': 'bluebottle.events.serializers.EventValidationSerializer',
    }


class EventSerializer(NoCommitMixin, EventListSerializer):
    contributions = FilteredRelatedField(many=True, filter_backend=ParticipantListFilter)

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = EventListSerializer.JSONAPIMeta.included_resources + [
            'contributions',
            'contributions.user'
        ]
        resource_name = 'activities/events'

    included_serializers = dict(
        EventListSerializer.included_serializers,
        **{
            'contributions': 'bluebottle.events.serializers.ParticipantSerializer',
        }
    )


class EventSubmitSerializer(ActivitySubmitSerializer):
    start_time = serializers.DateTimeField(
        required=True,
        error_messages={
            'blank': _('Start time is required'),
            'null': _('Start time is required')
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
        if self.initial_data['registration_deadline'] and \
                self.initial_data['registration_deadline'] > self.initial_data['start_date']:
            raise serializers.ValidationError("Registration deadline should be before start time")
        return data

    class Meta(ActivitySubmitSerializer.Meta):
        model = Event
        fields = ActivitySubmitSerializer.Meta.fields + (
            'start_time',
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
