from rest_framework_json_api import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import BaseContributorSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import (
    DeadlineParticipant,
    DeadlineRegistration,
    PeriodicParticipant,
    PeriodicRegistration,
    ScheduleParticipant,
    ScheduleRegistration,
    TeamScheduleParticipant,
    TeamScheduleRegistration
)
from bluebottle.utils.serializers import ResourcePermissionField


class ParticipantSerializer(BaseContributorSerializer):
    total_duration = serializers.DurationField(read_only=True)

    class Meta(BaseContributorSerializer.Meta):
        fields = BaseContributorSerializer.Meta.fields + (
            "total_duration",
            "registration",
        )
        meta_fields = BaseContributorSerializer.Meta.meta_fields + ("permissions",)

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        included_resources = ["user", "registration", "activity"]

    included_serializers = dict(
        BaseContributorSerializer.included_serializers,
        **{
            'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        }
    )


class DeadlineParticipantSerializer(ParticipantSerializer):
    permissions = ResourcePermissionField('deadline-participant-detail', view_args=('pk',))
    registration = ResourceRelatedField(queryset=DeadlineRegistration.objects.all())
    contributions = ResourceRelatedField(many=True, read_only=True)

    class Meta(ParticipantSerializer.Meta):
        model = DeadlineParticipant
        fields = ParticipantSerializer.Meta.fields + ("contributions",)

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = "contributors/time-based/deadline-participants"
        included_resources = ParticipantSerializer.JSONAPIMeta.included_resources + [
            "contributions",
        ]

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            "activity": "bluebottle.time_based.serializers.DeadlineActivitySerializer",
            "contributions": "bluebottle.time_based.serializers.TimeContributionSerializer",
            "registration": "bluebottle.time_based.serializers.DeadlineRegistrationSerializer",
        }
    )


class ScheduleParticipantSerializer(ParticipantSerializer):
    permissions = ResourcePermissionField('schedule-participant-detail', view_args=('pk',))
    registration = ResourceRelatedField(queryset=ScheduleRegistration.objects.all())

    class Meta(ParticipantSerializer.Meta):
        fields = ParticipantSerializer.Meta.fields + ("slot",)
        model = ScheduleParticipant

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = "contributors/time-based/schedule-participants"
        included_resources = ParticipantSerializer.JSONAPIMeta.included_resources + [
            "slot",
        ]

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
            "slot": "bluebottle.time_based.serializers.ScheduleSlotSerializer",
            "registration": "bluebottle.time_based.serializers.ScheduleRegistrationSerializer",
        }
    )


class TeamScheduleParticipantSerializer(ScheduleParticipantSerializer):
    permissions = ResourcePermissionField('team-schedule-participant-detail', view_args=('pk',))
    registration = ResourceRelatedField(queryset=TeamScheduleRegistration.objects.all())

    class Meta(ScheduleParticipantSerializer.Meta):
        model = TeamScheduleParticipant

    class JSONAPIMeta(ScheduleParticipantSerializer.JSONAPIMeta):
        resource_name = "contributors/time-based/team-schedule-participants"
        included_resources = ScheduleParticipantSerializer.JSONAPIMeta.included_resources + [
            "slot.location",
        ]

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
            "slot": "bluebottle.time_based.serializers.slots.TeamScheduleSlotSerializer",
            "slot.location": "bluebottle.geo.serializers.GeolocationSerializer",
            "registration": "bluebottle.time_based.serializers.TeamScheduleRegistrationSerializer",
        }
    )


class PeriodicParticipantSerializer(ParticipantSerializer):
    permissions = ResourcePermissionField('periodic-participant-detail', view_args=('pk',))
    registration = ResourceRelatedField(queryset=PeriodicRegistration.objects.all())
    contributions = ResourceRelatedField(many=True, read_only=True)

    class Meta(ParticipantSerializer.Meta):
        model = PeriodicParticipant
        fields = ParticipantSerializer.Meta.fields + ("contributions",)

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = "contributors/time-based/periodic-participants"
        included_resources = ParticipantSerializer.JSONAPIMeta.included_resources + [
            "contributions",
        ]

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            "activity": "bluebottle.time_based.serializers.PeriodicActivitySerializer",
            "contributions": "bluebottle.time_based.serializers.TimeContributionSerializer",
            "registration": "bluebottle.time_based.serializers.PeriodicRegistrationSerializer",
        }
    )


class ParticipantTransitionSerializer(TransitionSerializer):
    field = 'states'

    class JSONAPIMeta(object):
        included_resources = [
            'resource', 'resource.activity'
        ]


class DeadlineParticipantTransitionSerializer(ParticipantTransitionSerializer):
    resource = ResourceRelatedField(queryset=DeadlineParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DeadlineParticipantSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-participant-transitions'


class ScheduleParticipantTransitionSerializer(ParticipantTransitionSerializer):
    resource = ResourceRelatedField(queryset=ScheduleParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.ScheduleParticipantSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.ScheduleActivitySerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/schedule-participant-transitions'


class TeamScheduleParticipantTransitionSerializer(ParticipantTransitionSerializer):
    resource = ResourceRelatedField(queryset=TeamScheduleParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.TeamScheduleParticipantSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.ScheduleActivitySerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/team-schedule-participant-transitions'


class PeriodicParticipantTransitionSerializer(ParticipantTransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodicParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodicParticipantSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.PeriodicActivitySerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/periodic-participant-transitions'
