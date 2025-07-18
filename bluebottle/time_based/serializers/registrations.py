from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, validators
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer, PolymorphicModelSerializer

from bluebottle.activities.utils import BaseContributorSerializer
from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer, AvailableTransitionsField, CurrentStatusField
from bluebottle.time_based.models import (
    DeadlineRegistration, PeriodicRegistration,
    Registration, ScheduleRegistration,
    TeamScheduleRegistration, DateRegistration
)
from bluebottle.time_based.permissions import ParticipantDocumentPermission
from bluebottle.time_based.serializers import RelatedLinkFieldByStatus
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import ResourcePermissionField


class ContactEmailField(serializers.CharField):
    def __init__(self):
        super().__init__(read_only=True, source="user.email")

    def to_representation(self, value):
        user = self.context["request"].user
        if isinstance(self.parent.instance, list):
            activity = self.parent.instance[0].activity
        else:
            activity = self.parent.instance.activity

        if user.is_authenticated and (
            user.is_staff or
            user.is_superuser or
            user in activity.owners
        ):
            return super().to_representation(value)


class RegistrationSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = ResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    transitions = AvailableTransitionsField(source='states')
    current_status = CurrentStatusField(source='states.current_state')
    contact_email = ContactEmailField()

    document = PrivateDocumentField(
        required=False,
        allow_null=True,
        permissions=[ParticipantDocumentPermission]
    )

    class Meta(BaseContributorSerializer.Meta):
        model = Registration
        fields = [
            "transitions",
            "user",
            "activity",
            "contact_email",
            "permissions",
            "document",
            "answer",
            "participants",
        ]
        meta_fields = (
            'permissions', 'current_status', 'transitions'
        )
        validators = [
            validators.UniqueTogetherValidator(
                queryset=model.objects.all(),
                fields=('user', 'activity'),
                message=_("Registration for this user already exists on this activity.")
            )
        ]

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        included_resources = ['user', 'document', 'activity', 'participants']

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def to_representation(self, instance):
        result = super().to_representation(instance)

        user = self.context['request'].user

        if (
            user != instance.user and
            user not in instance.activity.owners and
            not user.is_staff and
            not user.is_superuser
        ):
            result['answer'] = None
            result['document'] = None

        return result

    def validate(self, data):
        if 'activity' in data and data['activity'].registration_flow == 'question':
            if not data.get('answer'):
                raise ValidationError({'answer': [_('This field is required')]})
        return data


class DateRegistrationSerializer(RegistrationSerializer):
    permissions = ResourcePermissionField('date-registration-detail', view_args=('pk',))
    participants = RelatedLinkFieldByStatus(
        many=True,
        read_only=True,
        related_link_view_name="date-registration-related-participants",
        related_link_url_kwarg="registration_id",
        statuses={
            "upcoming": ["new", "accepted", "running"],
            "passed": ["succeeded"],
            "total": ["new", "accepted", "running", "withdrawn", "succeeded", "failed"]
        },
    )

    class Meta(RegistrationSerializer.Meta):
        model = DateRegistration

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-registrations'
        included_resources = ['user', 'document', 'activity']

    included_serializers = dict(
        RegistrationSerializer.included_serializers.serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
            'document': 'bluebottle.time_based.serializers.registrations.RegistrationDocumentSerializer',
        }
    )


class DeadlineRegistrationSerializer(RegistrationSerializer):
    permissions = ResourcePermissionField('deadline-registration-detail', view_args=('pk',))
    participants = ResourceRelatedField(many=True, read_only=True, source='deadlineparticipant_set')

    class Meta(RegistrationSerializer.Meta):
        model = DeadlineRegistration

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-registrations'

    included_serializers = dict(
        RegistrationSerializer.included_serializers.serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
            'document': 'bluebottle.time_based.serializers.RegistrationDocumentSerializer',
            'participants': 'bluebottle.time_based.serializers.DeadlineParticipantSerializer'
        }
    )


class ScheduleRegistrationSerializer(RegistrationSerializer):
    permissions = ResourcePermissionField('schedule-registration-detail', view_args=('pk',))
    participants = ResourceRelatedField(many=True, read_only=True)

    class Meta(RegistrationSerializer.Meta):
        model = ScheduleRegistration

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/schedule-registrations'
        included_resources = ['user', 'document', 'activity']

    included_serializers = dict(
        RegistrationSerializer.included_serializers.serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.ScheduleActivitySerializer',
            'document': 'bluebottle.time_based.serializers.RegistrationDocumentSerializer',
            'participants': 'bluebottle.time_based.serializers.ScheduleParticipantSerializer'
        }
    )


class TeamScheduleRegistrationSerializer(RegistrationSerializer):
    permissions = ResourcePermissionField('team-schedule-registration-detail', view_args=('pk',))
    participants = ResourceRelatedField(many=True, read_only=True)
    team = ResourceRelatedField(read_only=True)

    class Meta(RegistrationSerializer.Meta):
        model = TeamScheduleRegistration
        fields = RegistrationSerializer.Meta.fields + [
            "team",
        ]

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/team-schedule-registrations'
        included_resources = [
            'user',
            'document',
            'activity',
            'participants',
            'team',
            'team.slots'
        ]

    included_serializers = dict(
        RegistrationSerializer.included_serializers.serializers,
        **{
            "activity": "bluebottle.time_based.serializers.ScheduleActivitySerializer",
            "document": "bluebottle.time_based.serializers.RegistrationDocumentSerializer",
            "team": "bluebottle.time_based.serializers.teams.TeamSerializer",
            "participants": "bluebottle.time_based.serializers.TeamScheduleParticipantSerializer",
            'team.slots': 'bluebottle.time_based.serializers.slots.TeamScheduleSlotSerializer'
        }
    )


class PeriodicRegistrationSerializer(RegistrationSerializer):
    permissions = ResourcePermissionField('periodic-registration-detail', view_args=('pk',))
    participants = ResourceRelatedField(many=True, read_only=True, source='periodicparticipant_set')
    total_hours = serializers.DurationField(read_only=True)
    total_slots = serializers.IntegerField(read_only=True)

    class Meta(RegistrationSerializer.Meta):
        model = PeriodicRegistration
        meta_fields = RegistrationSerializer.Meta.meta_fields + (
            "total_slots",
            "total_hours",
        )

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/periodic-registrations'

    included_serializers = dict(
        RegistrationSerializer.included_serializers.serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.PeriodicActivitySerializer',
            'document': 'bluebottle.time_based.serializers.RegistrationDocumentSerializer',
            'participants': 'bluebottle.time_based.serializers.PeriodicParticipantSerializer'
        }
    )


class PolymorphicRegistrationSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DeadlineRegistrationSerializer,
        ScheduleRegistrationSerializer,
        TeamScheduleRegistrationSerializer,
        PeriodicRegistrationSerializer,
        DateRegistrationSerializer
    ]

    class Meta(object):
        model = Registration
        meta_fields = (
            'created', 'updated', 'start', 'current_status', 'transitions', 'permissions'
        )


class RegistrationTransitionSerializer(TransitionSerializer):
    field = 'states'

    class JSONAPIMeta(object):
        included_resources = [
            'resource', 'resource.activity'
        ]


class DateRegistrationTransitionSerializer(RegistrationTransitionSerializer):
    resource = ResourceRelatedField(queryset=DateRegistration.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DateRegistrationSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.DateActivitySerializer',
    }

    class JSONAPIMeta(RegistrationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/date-registration-transitions'


class DeadlineRegistrationTransitionSerializer(RegistrationTransitionSerializer):
    resource = ResourceRelatedField(queryset=DeadlineRegistration.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.DeadlineRegistrationSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
    }

    class JSONAPIMeta(RegistrationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-registration-transitions'


class ScheduleRegistrationTransitionSerializer(RegistrationTransitionSerializer):
    resource = ResourceRelatedField(queryset=ScheduleRegistration.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.ScheduleRegistrationSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.ScheduleActivitySerializer',
    }

    class JSONAPIMeta(RegistrationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/schedule-registration-transitions'


class TeamScheduleRegistrationTransitionSerializer(RegistrationTransitionSerializer):
    resource = ResourceRelatedField(queryset=TeamScheduleRegistration.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.TeamScheduleRegistrationSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.ScheduleActivitySerializer',
    }

    class JSONAPIMeta(RegistrationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/team-schedule-registration-transitions'


class PeriodicRegistrationTransitionSerializer(RegistrationTransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodicRegistration.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodicRegistrationSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.PeriodicActivitySerializer',
    }

    class JSONAPIMeta(RegistrationTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/periodic-registration-transitions'


class RegistrationDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'registration-document'
    relationship = 'registration_set'
