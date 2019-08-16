from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer,
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


class LocationNotNull(object):
    message = _("Location is required or select 'is online'")

    def set_context(self, serializer_field):
        """
        This hook is called by the serializer instance,
        prior to the validation call being made.
        """
        self.instance = getattr(serializer_field.parent, 'instance', None)

    def __call__(self, value):
        if not self.instance.is_online and value is None:
            ValidationError(self.message, code='location')


class EventValidationSerializer(ActivityValidationSerializer):
    start_date = serializers.DateField()
    start_time = serializers.TimeField()
    duration = serializers.FloatField()
    registration_deadline = serializers.DateField(allow_null=True)
    is_online = serializers.BooleanField()
    location = RelatedField(
        queryset=Geolocation.objects.all(),
        allow_null=True,
        validators=[LocationNotNull()]
    )

    def validate(self, data):
        if not data['is_online'] and data['location'] is None:
            raise serializers.ValidationError(
                {'location': _("This field is required or select 'is online'")}
            )

        if data.get('registration_deadline') and data['registration_deadline'] > data['start_date']:
            raise serializers.ValidationError(
                {'registration_deadline': _('Registration deadline should be before start time')}
            )

        return data

    class Meta:
        model = Event
        fields = ActivityValidationSerializer.Meta.fields + (
            'start_date', 'start_time', 'is_online', 'location', 'duration',
            'registration_deadline',
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


class EventTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Event.objects.all())
    field = 'status'
    included_serializers = {
        'resource': 'bluebottle.events.serializers.EventSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', ]
        resource_name = 'event-transitions'
