from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity, Contribution
from bluebottle.members.models import Member
from bluebottle.transitions.serializers import AvailableTransitionsField
from bluebottle.utils.fields import FSMField, ValidationErrorsField, RequiredErrorsField

from bluebottle.utils.serializers import ResourcePermissionField


# This can't be in serializers because of circular imports
class BaseActivitySerializer(ModelSerializer):
    title = serializers.CharField(allow_blank=True, required=False)
    status = FSMField(read_only=True)
    review_status = FSMField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('pk',))
    owner = ResourceRelatedField(read_only=True)
    transitions = AvailableTransitionsField()
    review_transitions = AvailableTransitionsField()
    is_follower = serializers.SerializerMethodField()
    type = serializers.CharField(read_only=True, source='JSONAPIMeta.resource_name')
    stats = serializers.OrderedDict(read_only=True)

    slug = serializers.CharField(read_only=True)

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
    }

    def get_is_follower(self, instance):
        user = self.context['request'].user
        return bool(user.is_authenticated) and instance.followers.filter(user=user).exists()

    class Meta:
        model = Activity
        fields = (
            'type',  # Needed for old style API endpoints like pages / page blocks
            'slug',
            'id',
            'initiative',
            'owner',
            'title',
            'description',
            'is_follower',
            'status',
            'review_status',
            'stats',
            'errors',
            'required',
        )

        meta_fields = (
            'permissions',
            'transitions',
            'review_transitions',
            'created',
            'updated',
            'errors',
            'required',
        )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
        ]
        resource_name = 'activities'


class BaseActivityListSerializer(ModelSerializer):
    title = serializers.CharField(allow_blank=True, required=False)
    status = FSMField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('pk',))
    owner = ResourceRelatedField(read_only=True)
    is_follower = serializers.SerializerMethodField()
    type = serializers.CharField(read_only=True, source='JSONAPIMeta.resource_name')
    stats = serializers.OrderedDict(read_only=True)

    slug = serializers.CharField(read_only=True)

    included_serializers = {
        'initiative': 'bluebottle.initiatives.serializers.InitiativeListSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def get_is_follower(self, instance):
        user = self.context['request'].user
        return bool(user.is_authenticated) and instance.followers.filter(user=user).exists()

    class Meta:
        model = Activity
        fields = (
            'type',  # Needed for old style API endpoints like pages / page blocks
            'slug',
            'id',
            'initiative',
            'owner',
            'title',
            'description',
            'is_follower',
            'status',
            'stats',
        )

        meta_fields = (
            'permissions',
            'created',
            'updated',
        )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
            'initiative.image',
            'initiative.location',
            'initiative.place',
        ]
        resource_name = 'activities'


class ActivitySubmitSerializer(ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(required=True, queryset=Member.objects.all())
    title = serializers.CharField(required=True)
    description = serializers.CharField(
        required=True,
        error_messages={
            'blank': _('Description is required'),
            'null': _('Description is required')
        }
    )

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
    user = ResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    permissions = ResourcePermissionField('project_detail', view_args=('pk',))
    transitions = AvailableTransitionsField()

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
