from rest_framework.validators import UniqueTogetherValidator
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer,
)
from bluebottle.events.filters import ParticipantListFilter
from bluebottle.events.models import Event, Participant
from bluebottle.transitions.serializers import TransitionSerializer
from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField
from bluebottle.utils.serializers import NoCommitMixin


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
    field = 'transitions'
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


class EventListSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('event-detail', view_args=('pk',))

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
        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'initiative',
            'initiative.image',
            'location',
        ]
        resource_name = 'activities/events'

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
    }


class EventSerializer(NoCommitMixin, EventListSerializer):
    contributions = FilteredRelatedField(many=True, filter_backend=ParticipantListFilter)

    class Meta(EventListSerializer.Meta):
        fields = EventListSerializer.Meta.fields + (
            'contributions',
        )

    class JSONAPIMeta(EventListSerializer.JSONAPIMeta):
        included_resources = EventListSerializer.JSONAPIMeta.included_resources + [
            'contributions',
            'contributions.user'
        ]

    included_serializers = dict(
        EventListSerializer.included_serializers,
        **{
            'contributions': 'bluebottle.events.serializers.ParticipantSerializer',
        }
    )


class EventTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Event.objects.all())
    field = 'transitions'
    included_serializers = {
        'resource': 'bluebottle.events.serializers.EventSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', ]
        resource_name = 'event-transitions'
