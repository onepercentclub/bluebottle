from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity, Contribution
from bluebottle.members.models import Member
from bluebottle.transitions.serializers import AvailableTransitionsField
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import ResourcePermissionField


# This can't be in serializers because of circular imports
class BaseActivitySerializer(ModelSerializer):
    status = FSMField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('pk',))
    owner = ResourceRelatedField(read_only=True)
    contributions = ResourceRelatedField(many=True, read_only=True)

    transitions = AvailableTransitionsField(source='status')
    is_follower = serializers.SerializerMethodField()

    slug = serializers.CharField(read_only=True)

    included_serializers = {
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'contributions': 'bluebottle.activities.serializers.ContributionSerializer',
    }

    def get_is_follower(self, instance):
        user = self.context['request'].user
        return bool(user.is_authenticated) and instance.followers.filter(user=user).exists()

    class Meta:
        model = Activity
        fields = (
            'slug',
            'id',
            'initiative',
            'owner',
            'title',
            'description',
            'is_follower',
            'status',
            'contributions'
        )

        meta_fields = ('permissions', 'transitions', 'created', 'updated', )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
            'contributions',
        ]
        resource_name = 'activities'


class ActivitySubmitSerializer(ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(required=True, queryset=Member.objects.all())
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=True)

    class Meta:
        model = Activity
        fields = (
            'owner',
            'title',
            'description',
        )


# This can't be in serializers because of circular imports
class BaseContributionSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = ResourceRelatedField(read_only=True)

    permissions = ResourcePermissionField('project_detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='status')

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivitySerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta:
        model = Contribution
        fields = ('user', 'activity', 'status', )
        meta_fields = ('permissions', 'transitions', 'created', 'updated', )

    class JSONAPIMeta:
        included_resources = [
            'user',
            'activity',
        ]
        resource_name = 'contributions'
