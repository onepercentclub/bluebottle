from rest_framework_json_api.relations import ResourceRelatedField
from bluebottle.activities.utils import BaseContributorSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import DeadlineRegistration
from bluebottle.utils.serializers import ResourcePermissionField
from bluebottle.files.serializers import PrivateDocumentSerializer, PrivateDocumentField
from bluebottle.time_based.permissions import ParticipantDocumentPermission


class RegistrationSerializer(BaseContributorSerializer):
    document = PrivateDocumentField(required=False, allow_null=True, permissions=[ParticipantDocumentPermission])

    def __init__(self, *args, **kwargs):
        self.fields['permissions'] = ResourcePermissionField(self.detail_view_name, view_args=('pk',))

    class Meta(BaseContributorSerializer.Meta):
        fields = BaseContributorSerializer.Meta.fields 
        meta_fields = BaseContributorSerializer.Meta.meta_fields + (
            'permissions', 'document', 'motivation'
        )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        included_resources = ['user', 'document']

    included_serializers = dict(
        BaseContributorSerializer.included_serializers,
        **{
            'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        }
    )


class DeadlineRegistrationSerializer(RegistrationSerializer):
    detail_view_name = 'deadline-registration-detail'

    class Meta(RegistrationSerializer.Meta):
        model = DeadlineRegistration

    class JSONAPIMeta(RegistrationSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-registrations'

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
