from django.urls import reverse

from rest_framework.validators import UniqueTogetherValidator
from rest_framework import serializers

from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer,
    BaseActivityListSerializer, BaseTinyActivitySerializer
)
from bluebottle.events.filters import ParticipantListFilter
from bluebottle.events.models import Event, Participant
from bluebottle.transitions.serializers import TransitionSerializer
from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField
from bluebottle.utils.serializers import NoCommitMixin


class ParticipantListSerializer(BaseContributionSerializer):

    class Meta(BaseContributionSerializer.Meta):
        model = Participant
        fields = BaseContributionSerializer.Meta.fields + ('time_spent', )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/participants'
        included_resources = [
            'user',
            'activity'
        ]

    included_serializers = {
        'activity': 'bluebottle.events.serializers.TinyEventSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


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
        'activity': 'bluebottle.events.serializers.EventListSerializer',
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


class EventListSerializer(BaseActivityListSerializer):
    permissions = ResourcePermissionField('event-detail', view_args=('pk',))

    class Meta(BaseActivityListSerializer.Meta):
        model = Event
        fields = BaseActivityListSerializer.Meta.fields + (
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

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        included_resources = [
            'location',
        ]
        resource_name = 'activities/events'

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class EventSerializer(NoCommitMixin, BaseActivitySerializer):
    permissions = ResourcePermissionField('event-detail', view_args=('pk',))
    contributions = FilteredRelatedField(many=True, filter_backend=ParticipantListFilter)
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        return {
            'ical': reverse('event-ical', args=(instance.pk, )),
            'google': instance.google_calendar_link,
            'outlook': instance.outlook_link,
        }

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
            'contributions',
            'links'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'location',
            'contributions',
            'contributions.user'
        ]
        resource_name = 'activities/events'

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'contributions': 'bluebottle.events.serializers.ParticipantSerializer',
        }
    )


class TinyEventSerializer(BaseTinyActivitySerializer):

    class Meta(BaseTinyActivitySerializer.Meta):
        model = Event
        fields = BaseTinyActivitySerializer.Meta.fields + ('start_time', 'start_date', 'duration')

    class JSONAPIMeta(BaseTinyActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/events'


class EventTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Event.objects.all())
    field = 'transitions'
    included_serializers = {
        'resource': 'bluebottle.events.serializers.EventSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', ]
        resource_name = 'event-transitions'
