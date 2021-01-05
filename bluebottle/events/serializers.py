from builtins import object
from rest_framework.validators import UniqueTogetherValidator
from rest_framework import serializers

from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributorSerializer,
    BaseActivityListSerializer, BaseTinyActivitySerializer
)
from bluebottle.events.filters import ParticipantListFilter
from bluebottle.events.models import Event, Participant
from bluebottle.utils.utils import reverse_signed
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.utils.serializers import ResourcePermissionField, FilteredRelatedField
from bluebottle.utils.serializers import NoCommitMixin


class ParticipantListSerializer(BaseContributorSerializer):

    class Meta(BaseContributorSerializer.Meta):
        model = Participant
        fields = BaseContributorSerializer.Meta.fields + ('time_spent', )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/participants'
        included_resources = [
            'user',
            'activity'
        ]

    included_serializers = {
        'activity': 'bluebottle.events.serializers.TinyEventSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class ParticipantSerializer(BaseContributorSerializer):

    class Meta(BaseContributorSerializer.Meta):
        model = Participant
        fields = BaseContributorSerializer.Meta.fields + ('time_spent', )

        validators = [
            UniqueTogetherValidator(
                queryset=Participant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/participants'
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
    field = 'states'
    included_serializers = {
        'resource': 'bluebottle.events.serializers.ParticipantSerializer',
        'resource.activity': 'bluebottle.events.serializers.EventSerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'contributors/participant-transitions'
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
            'start',
            'local_start',
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
    contributors = FilteredRelatedField(many=True, filter_backend=ParticipantListFilter)
    links = serializers.SerializerMethodField()

    def get_links(self, instance):
        return {
            'ical': reverse_signed('event-ical', args=(instance.pk, )),
            'google': instance.google_calendar_link,
            'outlook': instance.outlook_link,
        }

    def get_fields(self):
        fields = super(EventSerializer, self).get_fields()
        user = self.context['request'].user

        if (
            not user.is_authenticated or (
                self.instance and (
                    user not in [
                        self.instance.owner,
                        self.instance.initiative.owner,
                        self.instance.initiative.activity_manager
                    ] and
                    not len(self.instance.participants.filter(user=user))
                )
            )
        ):
            del fields['online_meeting_url']

        return fields

    class Meta(BaseActivitySerializer.Meta):
        model = Event
        fields = BaseActivitySerializer.Meta.fields + (
            'capacity',
            'start',
            'local_start',
            'duration',
            'is_online',
            'online_meeting_url',
            'location',
            'location_hint',
            'permissions',
            'registration_deadline',
            'contributors',
            'links'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'location',
            'contributors',
            'contributors.user'
        ]
        resource_name = 'activities/events'

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'contributors': 'bluebottle.events.serializers.ParticipantSerializer',
        }
    )


class TinyEventSerializer(BaseTinyActivitySerializer):

    class Meta(BaseTinyActivitySerializer.Meta):
        model = Event
        fields = BaseTinyActivitySerializer.Meta.fields + ('start', 'local_start', 'duration')

    class JSONAPIMeta(BaseTinyActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/events'


class EventTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Event.objects.all())
    field = 'states'
    included_serializers = {
        'resource': 'bluebottle.events.serializers.EventSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'event-transitions'
