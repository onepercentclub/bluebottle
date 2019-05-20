from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity, Contribution
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import (
    ResourcePermissionField,
    FSMSerializer)


# This can't be in serializers because of circular imports
class BaseActivitySerializer(ModelSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    status = FSMField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('slug',))
    type = serializers.SerializerMethodField()
    owner = ResourceRelatedField(read_only=True)

    def get_type(self, instance):
        return instance._meta.model_name

    class Meta:
        model = Activity
        fields = (
            'id',
            'initiative',
            'status',
            'owner',
            'title',
            'description',
            'type'
        )

    included_serializers = {
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative'
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
