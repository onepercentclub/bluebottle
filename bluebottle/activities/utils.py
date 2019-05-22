from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity, Contribution
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.transitions.serializers import AvailableTransitionsField
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import (
    ResourcePermissionField,
    FSMSerializer)


# This can't be in serializers because of circular imports
class BaseActivitySerializer(ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    status = FSMField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('slug',))
    owner = ResourceRelatedField(read_only=True)

    transitions = AvailableTransitionsField(source='status')
    is_follower = serializers.SerializerMethodField()

    included_serializers = {
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'contributions': 'bluebottle.activities.serializers.ContributionSerializer',
    }

    def get_is_follower(self, instance):
        return instance.followers.filter(user=self.context['request'].user).exists()

    class Meta:
        model = Activity
        fields = (
            'id',
            'initiative',
            'owner',
            'title',
            'description',
        )

        meta_fields = ('permissions', 'transitions', 'status', 'created', 'updated', 'is_follower', )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
            'contributions',
        ]
        resource_name = 'activities'


# This can't be in serializers because of circular imports
class BaseContributionSerializer(FSMSerializer):
    status = FSMField(read_only=True)
    user = UserPreviewSerializer()

    permissions = ResourcePermissionField('project_detail', view_args=('slug',))

    class Meta:
        model = Contribution
        fields = ('status', 'user', 'permissions', )
