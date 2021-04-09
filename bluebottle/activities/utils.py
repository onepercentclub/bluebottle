from builtins import object

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from geopy.distance import distance, lonlat

from bluebottle.activities.models import Activity, Contributor, Contribution
from bluebottle.impact.models import ImpactGoal
from bluebottle.members.models import Member
from bluebottle.fsm.serializers import AvailableTransitionsField
from bluebottle.utils.fields import FSMField, ValidationErrorsField, RequiredErrorsField

from bluebottle.utils.serializers import ResourcePermissionField


class MatchingPropertiesField(serializers.ReadOnlyField):
    def __init__(self, **kwargs):
        kwargs['source'] = '*'
        super().__init__(**kwargs)

    def to_representation(self, obj):
        user = self.context['request'].user
        matching = {'skill': False, 'theme': False, 'location': False}

        if user.is_authenticated:
            if 'skills' not in self.context:
                self.context['skills'] = user.skills.all()

            if 'themes' not in self.context:
                self.context['themes'] = user.favourite_themes.all()

            if 'location' not in self.context:
                self.context['location'] = user.location or user.place

            try:
                if obj.expertise in self.context['skills']:
                    matching['skill'] = True
            except AttributeError:
                pass

            try:
                if obj.initiative.theme in self.context['themes']:
                    matching['theme'] = True
            except AttributeError:
                pass

            positions = []
            try:
                if obj.location:
                    positions = [obj.location.position.tuple]
            except AttributeError:
                try:
                    positions = [
                        slot.location.position.tuple for slot in obj.slots.all() if slot.location
                    ]
                except AttributeError:
                    pass

            if self.context['location'] and positions:
                dist = min(
                    distance(
                        lonlat(*pos),
                        lonlat(*self.context['location'].position.tuple)
                    ) for pos in positions
                )

                if dist.km < 20:
                    matching['location'] = True

        return matching


# This can't be in serializers because of circular imports
class BaseActivitySerializer(ModelSerializer):
    title = serializers.CharField(allow_blank=True, required=False)
    status = FSMField(read_only=True)
    owner = ResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('activity-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')
    is_follower = serializers.SerializerMethodField()
    type = serializers.CharField(read_only=True, source='JSONAPIMeta.resource_name')
    stats = serializers.OrderedDict(read_only=True)
    goals = ResourceRelatedField(required=False, many=True, queryset=ImpactGoal.objects.all())
    slug = serializers.CharField(read_only=True)

    matching_properties = MatchingPropertiesField()

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'goals.type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
        'initiative.activity_manager': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative.promoter': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    def get_is_follower(self, instance):
        user = self.context['request'].user
        return bool(user.is_authenticated) and instance.followers.filter(user=user).exists()

    class Meta(object):
        model = Activity
        fields = (
            'type',  # Needed for old style API endpoints like pages / page blocks
            'slug',
            'id',
            'image',
            'video_url',
            'initiative',
            'goals',
            'owner',
            'title',
            'description',
            'is_follower',
            'status',
            'stats',
            'errors',
            'required',
            'goals'
        )

        meta_fields = (
            'permissions',
            'transitions',
            'created',
            'updated',
            'errors',
            'required',
            'matching_properties',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
            'image',
            'initiative',
            'goals',
            'goals.type',
            'initiative.place',
            'initiative.location',
            'initiative.activity_manager',
            'initiative.promoter',
            'initiative.image',
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
    goals = ResourceRelatedField(required=False, many=True, queryset=ImpactGoal.objects.all())
    slug = serializers.CharField(read_only=True)
    matching_properties = MatchingPropertiesField()

    included_serializers = {
        'initiative': 'bluebottle.initiatives.serializers.InitiativeListSerializer',
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'goals.type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
    }

    def get_is_follower(self, instance):
        user = self.context['request'].user
        return bool(user.is_authenticated) and instance.followers.filter(user=user).exists()

    class Meta(object):
        model = Activity
        fields = (
            'type',  # Needed for old style API endpoints like pages / page blocks
            'slug',
            'id',
            'image',
            'initiative',
            'owner',
            'title',
            'description',
            'is_follower',
            'status',
            'stats',
            'goals',
        )

        meta_fields = (
            'permissions',
            'created',
            'updated',
            'matching_properties',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
            'initiative',
            'image',
            'initiative.image',
            'initiative.location',
            'initiative.place',
            'goals',
            'goals.type',
        ]
        resource_name = 'activities'


class BaseTinyActivitySerializer(ModelSerializer):
    title = serializers.CharField(allow_blank=True, required=False)
    slug = serializers.CharField(read_only=True)

    class Meta(object):
        model = Activity
        fields = (
            'slug',
            'id',
            'title',
        )

        meta_fields = (
            'created',
            'updated',
        )

    class JSONAPIMeta(object):
        pass


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

    class Meta(object):
        model = Activity
        fields = (
            'owner',
            'title',
            'description',
        )


# This can't be in serializers because of circular imports
class BaseContributorListSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = ResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.TinyActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(object):
        model = Contributor
        fields = ('user', 'activity', 'status', 'created', 'updated', )
        meta_fields = ('created', 'updated', )

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
        ]
        resource_name = 'contributors'


# This can't be in serializers because of circular imports
class BaseContributorSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    user = ResourceRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))
    transitions = AvailableTransitionsField(source='states')

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(object):
        model = Contributor
        fields = ('user', 'activity', 'status', )
        meta_fields = ('permissions', 'transitions', 'created', 'updated', )

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
        ]
        resource_name = 'contributors'


# This can't be in serializers because of circular imports
class BaseContributionSerializer(ModelSerializer):
    status = FSMField(read_only=True)

    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))

    class Meta(object):
        model = Contribution
        fields = ('value', 'status', )
        meta_fields = ('permissions', 'created', )

    class JSONAPIMeta(object):
        resource_name = 'contributors'
