from rest_framework import serializers

from bluebottle.activities.models import Activity
from bluebottle.members.serializers import UserPreviewSerializer
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import (
    ResourcePermissionField, FSMSerializer
)


class BaseActivitySerializer(FSMSerializer):
    id = serializers.CharField(source='slug', read_only=True)
    status = FSMField(read_only=True)
    owner = UserPreviewSerializer()

    permissions = ResourcePermissionField('project_detail', view_args=('slug',))
    type = serializers.SerializerMethodField()

    def get_type(self, instance):
        return instance._meta.model_name

    class Meta:
        fields = (
            'id', 'status', 'owner', 'title', 'description', 'type', 'permissions',
        )

    def create(self, **validate_data):
        instance = super(BaseActivitySerializer, self).create(**validate_data)
        instance.submitted()

        return instance

    def update(self, instance, **validate_data):
        instance = super(BaseActivitySerializer, self).update(self, instance, **validate_data)
        if instance.status == 'needs_work':
            instance.submitted()

        return instance


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
