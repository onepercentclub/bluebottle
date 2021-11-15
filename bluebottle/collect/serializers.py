from rest_framework import serializers
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
from bluebottle.utils.utils import reverse_signed


class CollectActivitySerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('collect-activity-detail', view_args=('pk',))
    links = serializers.SerializerMethodField()
    collect_type = ResourceRelatedField(
        queryset=CollectType.objects,
        required=False,
        source='type'
    )

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

    def get_links(self, instance):
        if instance.start and instance.end:
            return {
                'ical': reverse_signed('collect-ical', args=(instance.pk, )),
                'google': instance.google_calendar_link,
            }
        else:
            return {}

    def get_contributors(self, instance):
        user = self.context['request'].user
        return [
            contributor for contributor in instance.contributors.exclude(user=None) if (
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
            'realized',
            'contributors_export_url',
            'location',
            'location_hint',
            'collect_type',
            'target',
            'realized',
            'enable_impact',
            'links'
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/collects'
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'my_contributor',
            'location',
            'collect_type'
        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'my_contributor': 'bluebottle.collect.serializers.CollectContributorSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'collect_type': 'bluebottle.collect.serializers.CollectTypeSerializer',

        }
    )


class CollectActivityListSerializer(BaseActivityListSerializer):
    permissions = ResourcePermissionField('collect-activity-detail', view_args=('pk',))

    collect_type = ResourceRelatedField(
        queryset=CollectType.objects,
        required=False,
        source='type'
    )

    class Meta(BaseActivityListSerializer.Meta):
        model = CollectActivity
        fields = BaseActivityListSerializer.Meta.fields + (
            'start',
            'end',
            'realized',
            'collect_type'
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/collects'
        included_resources = BaseActivityListSerializer.JSONAPIMeta.included_resources + [
            'collect_type',
        ]

    included_serializers = dict(
        BaseActivityListSerializer.included_serializers,
        **{
            'collect_type': 'bluebottle.collect.serializers.CollectTypeSerializer',
        }
    )


class CollectActivityTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=CollectActivity.objects.all())
    included_serializers = {
        'resource': 'bluebottle.collect.serializers.CollectActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/collect-transitions'


class CollectContributorSerializer(BaseContributorSerializer):
    activity = ResourceRelatedField(
        queryset=CollectActivity.objects.all()
    )
    permissions = ResourcePermissionField('collect-contributor-detail', view_args=('pk',))

    class Meta(BaseContributorSerializer.Meta):
        model = CollectContributor
        meta_fields = BaseContributorSerializer.Meta.meta_fields + ('permissions', )
        fields = BaseContributorSerializer.Meta.fields

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/collect/contributors'
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
        resource_name = 'contributors/collect/contributor-transitions'
        included_resources = [
            'resource',
        ]


class CollectTypeSerializer(ModelSerializer):

    class Meta(object):
        model = CollectType
        fields = ('id', 'name', 'unit', 'unit_plural')

    class JSONAPIMeta(object):
        resource_name = 'activities/collect-types'
