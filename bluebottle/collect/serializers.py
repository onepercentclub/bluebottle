from rest_framework.serializers import ModelSerializer
from rest_framework_json_api.relations import (
    ResourceRelatedField,
    SerializerMethodResourceRelatedField
)

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseActivityListSerializer, BaseContributorSerializer
)
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.collect.models import CollectActivity, CollectContributor, CollectType
from bluebottle.collect.states import CollectContributorStateMachine
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.time_based.permissions import CanExportParticipantsPermission
from bluebottle.utils.serializers import ResourcePermissionField


class CollectActivitySerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('collect-activity-detail', view_args=('pk',))
    my_contributor = SerializerMethodResourceRelatedField(
        model=CollectContributor,
        read_only=True,
        source='get_my_contributor'
    )

    contributors = SerializerMethodResourceRelatedField(
        model=CollectContributor,
        many=True,
        related_link_view_name='related-collect-contributors',
        related_link_url_kwarg='activity_id'
    )

    contributors_export_url = PrivateFileSerializer(
        'collect-contributors-export',
        url_args=('pk', ),
        filename='contributors.csv',
        permission=CanExportParticipantsPermission,
        read_only=True
    )

    def get_contributors(self, instance):
        user = self.context['request'].user
        return [
            contributor for contributor in instance.contributors.all() if (
                isinstance(contributor, CollectContributor) and (
                    contributor.status in [
                        CollectContributorStateMachine.new.value,
                        CollectContributorStateMachine.accepted.value,
                        CollectContributorStateMachine.succeeded.value
                    ] or
                    user in (instance.owner, instance.initiative.owner, contributor.user)
                )
            )
        ]

    def get_my_contributor(self, instance):
        user = self.context['request'].user
        if user.is_authenticated:
            return instance.contributors.filter(user=user).instance_of(CollectContributor).first()

    class Meta(BaseActivitySerializer.Meta):
        model = CollectActivity
        fields = BaseActivitySerializer.Meta.fields + (
            'my_contributor',
            'contributors',
            'start',
            'end',
            'contributors_export_url',
            'location',
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/collects'
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'my_contributor',
            'location'
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'my_contributor': 'bluebottle.collect.serializers.CollectContributorSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class CollectActivityListSerializer(BaseActivityListSerializer):
    permissions = ResourcePermissionField('collect-activity-detail', view_args=('pk',))

    class Meta(BaseActivityListSerializer.Meta):
        model = CollectActivity
        fields = BaseActivityListSerializer.Meta.fields + (
            'start',
            'end',
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/collects'


class CollectActivityTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=CollectActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.collect.serializers.CollectActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/collect-activity-transitions'


class CollectContributorSerializer(BaseContributorSerializer):
    activity = ResourceRelatedField(
        queryset=CollectActivity.objects.all()
    )
    permissions = ResourcePermissionField('collect-contributor-detail', view_args=('pk',))

    class Meta(BaseContributorSerializer.Meta):
        model = CollectContributor
        meta_fields = BaseContributorSerializer.Meta.meta_fields + ('permissions', )
        fields = BaseContributorSerializer.Meta.fields + ('value',)

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/collect/contributor'
        included_resources = [
            'user',
            'activity',
        ]

    included_serializers = {
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity': 'bluebottle.collect.serializers.CollectActivitySerializer',
    }


class CollectContributorListSerializer(CollectContributorSerializer):
    pass


class CollectContributorTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=CollectContributor.objects.all())
    field = 'states'

    included_serializers = {
        'resource': 'bluebottle.collect.serializers.CollectContributorSerializer',
    }

    class JSONAPIMeta(object):
        resource_name = 'contributors/collect/collect-contributor-transitions'
        included_resources = [
            'resource',
        ]


class CollectTypeSerializer(ModelSerializer):

    class Meta(object):
        model = CollectType
        fields = ('id', 'name', 'description')

    class JSONAPIMeta(object):
        resource_name = 'activities/collect-types'
