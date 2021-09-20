from rest_framework.validators import UniqueTogetherValidator

from rest_framework_json_api.relations import (
    ResourceRelatedField,
    SerializerMethodResourceRelatedField
)

from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer, BaseContributorSerializer
)
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.deeds.states import DeedParticipantStateMachine
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.permissions import CanExportParticipantsPermission
from bluebottle.utils.serializers import ResourcePermissionField


class DeedSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('deed-detail', view_args=('pk',))
    my_contributor = SerializerMethodResourceRelatedField(
        model=DeedParticipant,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = SerializerMethodResourceRelatedField(
        model=DeedParticipant,
        many=True,
        related_link_view_name='related-deed-participants',
        related_link_url_kwarg='activity_id'
    )

    participants_export_url = PrivateFileSerializer(
        'deed-participant-export',
        url_args=('pk', ),
        filename='participant.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    def get_contributors(self, instance):
        user = self.context['request'].user
        return [
            contributor for contributor in instance.contributors.all() if (
                isinstance(contributor, DeedParticipant) and (
                    contributor.status in [
                        DeedParticipantStateMachine.new.value,
                        DeedParticipantStateMachine.accepted.value,
                        DeedParticipantStateMachine.succeeded.value
                    ] or
                    user in (instance.owner, instance.initiative.owner, contributor.user)
                )
            )
        ]

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(DeedParticipant).first()

    class Meta(BaseActivitySerializer.Meta):
        model = Deed
        fields = BaseActivitySerializer.Meta.fields + (
            'my_contributor',
            'contributors',
            'start',
            'end',
            'target',
            'participants_export_url',
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/deeds'
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'my_contributor',
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'my_contributor': 'bluebottle.deeds.serializers.DeedParticipantSerializer',
        }
    )


class DeedListSerializer(BaseActivityListSerializer):
    permissions = ResourcePermissionField('deed-detail', view_args=('pk',))

    class Meta(BaseActivityListSerializer.Meta):
        model = Deed
        fields = BaseActivityListSerializer.Meta.fields + (
            'start',
            'end',
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/deeds'


class DeedTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Deed.objects.all())
    included_serializers = {
        'resource': 'bluebottle.deeds.serializers.DeedSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/deed-transitions'


class DeedParticipantSerializer(BaseContributorSerializer):
    activity = ResourceRelatedField(
        queryset=Deed.objects.all()
    )
    permissions = ResourcePermissionField('deed-participant-detail', view_args=('pk',))

    class Meta(BaseContributorSerializer.Meta):
        model = DeedParticipant
        meta_fields = BaseContributorSerializer.Meta.meta_fields + ('permissions', )

        validators = [
            UniqueTogetherValidator(
                queryset=DeedParticipant.objects.all(),
                fields=('activity', 'user')
            )
        ]

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/deeds/participants'
        included_resources = [
            'user', 'activity',
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity': 'bluebottle.deeds.serializers.DeedSerializer',
    }


class DeedParticipantListSerializer(DeedParticipantSerializer):
    pass


class DeedParticipantTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=DeedParticipant.objects.all())
    field = 'states'

    included_serializers = {
        'resource': 'bluebottle.deeds.serializers.DeedParticipantSerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'contributors/deeds/participant-transitions'
        included_resources = [
            'resource',
        ]
