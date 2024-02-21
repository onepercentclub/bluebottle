from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.activities.utils import BaseContributorSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.models import DeadlineParticipant, DeadlineRegistration, PeriodicParticipant, PeriodicRegistration
from bluebottle.utils.serializers import ResourcePermissionField


class ParticipantSerializer(BaseContributorSerializer):
    class Meta(BaseContributorSerializer.Meta):
        fields = BaseContributorSerializer.Meta.fields + ('registration', )
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
    permissions = ResourcePermissionField('deadline-participant-detail', view_args=('pk',))
    registration = ResourceRelatedField(queryset=DeadlineRegistration.objects.all())

    class Meta(ParticipantSerializer.Meta):
        model = DeadlineParticipant

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/deadline-participants'
        included_resources = ParticipantSerializer.JSONAPIMeta.included_resources + ['activity']

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.DeadlineActivitySerializer',
        }
    )


class PeriodicParticipantSerializer(ParticipantSerializer):
    permissions = ResourcePermissionField('periodic-participant-detail', view_args=('pk',))
    registration = ResourceRelatedField(queryset=PeriodicRegistration.objects.all())

    class Meta(ParticipantSerializer.Meta):
        model =  PeriodicParticipant

    class JSONAPIMeta(ParticipantSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/periodic-participants'
        included_resources = ParticipantSerializer.JSONAPIMeta.included_resources + ['activity']

    included_serializers = dict(
        ParticipantSerializer.included_serializers,
        **{
            'activity': 'bluebottle.time_based.serializers.PeriodicActivitySerializer',
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


class PeriodicParticipantTransitionSerializer(ParticipantTransitionSerializer):
    resource = ResourceRelatedField(queryset=PeriodicParticipant.objects.all())
    included_serializers = {
        'resource': 'bluebottle.time_based.serializers.PeriodicParticipantSerializer',
        'resource.activity': 'bluebottle.time_based.serializers.PeriodicActivitySerializer',
    }

    class JSONAPIMeta(ParticipantTransitionSerializer.JSONAPIMeta):
        resource_name = 'contributors/time-based/periodic-participant-transitions'
