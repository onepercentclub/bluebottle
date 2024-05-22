from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.utils import BaseContributorSerializer
from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer, AvailableTransitionsField, CurrentStatusField
from bluebottle.time_based.models import (
    DeadlineRegistration, PeriodicRegistration,
    Registration, ScheduleRegistration,
    TeamScheduleRegistration
)
from bluebottle.time_based.permissions import ParticipantDocumentPermission
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import ResourcePermissionField, AnonymizedResourceRelatedField


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
            user == activity.owner or
            user == activity.initiative.owner or
            user in activity.initiative.activity_managers.all()
        ):
            return super().to_representation(value)


class RegistrationSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = AnonymizedResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())
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

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        included_resources = ['user', 'document', 'activity', 'participants']

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def to_representation(self, instance):
        result = super().to_representation(instance)

        user = self.context['request'].user

        privileged_users = [instance.user, instance.activity.owner] + list(
            instance.activity.initiative.activity_managers.all()
        )
        if (
            user not in privileged_users and
            not user.is_staff and
            not user.is_superuser
        ):
            del result['answer']
            del result['document']

        return result

    def validate(self, data):
        if 'activity' in data and data['activity'].registration_flow == 'question':
            if not data.get('answer'):
                raise ValidationError({'answer': [_('This field is required')]})
        return data


class DeadlineRegistrationSerializer(RegistrationSerializer):
    permissions = ResourcePermissionField('deadline-registration-detail', view_args=('pk',))
    participants = ResourceRelatedField(many=True, read_only=True, source='deadlineparticipant_set')

    class Meta(RegistrationSerializer.Meta):
        model = DeadlineRegistration

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-registrations'

    included_serializers = dict(
        RegistrationSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
            'document': 'bluebottle.time_based.serializers.DeadlineRegistrationDocumentSerializer',
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
        RegistrationSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.ScheduleActivitySerializer',
            'document': 'bluebottle.time_based.serializers.ScheduleRegistrationDocumentSerializer',
            'participants': 'bluebottle.time_based.serializers.ScheduleParticipantSerializer'
        }
    )


class TeamScheduleRegistrationSerializer(RegistrationSerializer):
    permissions = ResourcePermissionField('team-schedule-registration-detail', view_args=('pk',))
    participants = ResourceRelatedField(many=True, read_only=True)

    def to_representation(self, instance):
        result = super().to_representation(instance)

        user = self.context['request'].user
        if (user not in [
            instance.user,
            instance.activity.owner,
        ] and user not in instance.activity.initiative.activity_managers.all() and
            not user.is_staff and
            not user.is_superuser
        ):
            # del result['answer']
            # del result['document']
            del result['invite_code']

        return result

    class Meta(RegistrationSerializer.Meta):
        model = TeamScheduleRegistration
        fields = RegistrationSerializer.Meta.fields + [
            "invite_code",
        ]

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/team-schedule-registrations'

    included_serializers = dict(
        RegistrationSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.ScheduleActivitySerializer',
            'document': 'bluebottle.time_based.serializers.ScheduleRegistrationDocumentSerializer',
            'participants': 'bluebottle.time_based.serializers.TeamScheduleParticipantSerializer'
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
        RegistrationSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.PeriodicActivitySerializer',
            'document': 'bluebottle.time_based.serializers.PeriodicRegistrationDocumentSerializer',
            'participants': 'bluebottle.time_based.serializers.PeriodicParticipantSerializer'
        }
    )


class RegistrationTransitionSerializer(TransitionSerializer):
    field = 'states'

    class JSONAPIMeta(object):
        included_resources = [
            'resource', 'resource.activity'
        ]


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


class DeadlineRegistrationDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'deadline-registration-document'
    relationship = 'registration_set'


class ScheduleRegistrationDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'schedule-registration-document'
    relationship = 'registration_set'


class PeriodicRegistrationDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'periodic-registration-document'
    relationship = 'registration_set'
