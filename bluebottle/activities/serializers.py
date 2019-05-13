from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import (
    ResourcePermissionField, FSMSerializer
)


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


class ActivitySerializer(BaseActivitySerializer):
    id = serializers.CharField(source='slug', read_only=True)
    data = serializers.SerializerMethodField()

    def get_data(self, instance):
        return instance.preview_data  # TODO: Use serializers

    class Meta:
        model = Activity
        fields = BaseActivitySerializer.Meta.fields + ('data', )


class ContributionSerializer(FSMSerializer):
    status = FSMField(read_only=True)
    user = UserPreviewSerializer()

    permissions = ResourcePermissionField('project_detail', view_args=('slug',))

    class Meta:
        fields = ('status', 'user', 'permissions', )
