from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.utils import BaseContributorSerializer
from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.fsm.serializers import TransitionSerializer, AvailableTransitionsField, CurrentStatusField
from bluebottle.time_based.models import DeadlineRegistration, Registration
from bluebottle.time_based.permissions import ParticipantDocumentPermission
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import ResourcePermissionField, AnonymizedResourceRelatedField


class RegistrationSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = AnonymizedResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())
    team = ResourceRelatedField(read_only=True)
    transitions = AvailableTransitionsField(source='states')
    current_status = CurrentStatusField(source='states.current_state')

    document = PrivateDocumentField(required=False, allow_null=True, permissions=[ParticipantDocumentPermission])

    class Meta(BaseContributorSerializer.Meta):
        model = Registration
        fields = [
            'transitions',
            'user',
            'activity',
            'permissions',
            'document',
            'answer'
        ]
        meta_fields = (
            'permissions', 'status', 'transitions', 'current_status'
        )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        included_resources = ['user', 'document', 'activity']

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class DeadlineRegistrationSerializer(RegistrationSerializer):
    permissions = ResourcePermissionField('deadline-registration-detail', view_args=('pk',))

    class Meta(RegistrationSerializer.Meta):
        model = DeadlineRegistration

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-registrations'
        included_resources = [
            'user',
            'activity',
        ]

    included_serializers = dict(
        RegistrationSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
            'document': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
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


class DeadlineRegistrationDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'deadline-registration-document'
    relationship = 'deadlineparticipant_set'
