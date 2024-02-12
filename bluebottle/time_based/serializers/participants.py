from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import BaseContributorSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import DeadlineParticipant
from bluebottle.utils.serializers import ResourcePermissionField


class ParticipantSerializer(BaseContributorSerializer):
    def __init__(self, *args, **kwargs):
        self.fields['permissions'] = ResourcePermissionField(self.detail_view_name, view_args=('pk',))

    class Meta(BaseContributorSerializer.Meta):
        fields = BaseContributorSerializer.Meta.fields
        meta_fields = BaseContributorSerializer.Meta.meta_fields + ('permissions',)

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        included_resources = ['user']

    included_serializers = dict(
        BaseContributorSerializer.included_serializers,
        **{
            'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        }
    )


class DeadlineParticipantSerializer(ParticipantSerializer):
    detail_view_name = 'deadline-participant-detail'

    class Meta(ParticipantSerializer.Meta):
        model = DeadlineParticipant

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-participants'

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
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
