from builtins import object

from django.db.models import Sum, Count
from django.utils.translation import ugettext_lazy as _
from moneyed import Money
from rest_framework import serializers
from rest_framework_json_api.relations import (
    ResourceRelatedField
)
from rest_framework_json_api.serializers import ModelSerializer
from rest_framework_json_api.relations import (
    SerializerMethodResourceRelatedField
)

from bluebottle.activities.models import EffortContribution, Activity
from bluebottle.activities.states import ActivityStateMachine
from bluebottle.bluebottle_drf2.serializers import (
    ImageSerializer as OldImageSerializer, SorlImageField
)
from bluebottle.categories.models import Category
from bluebottle.clients import properties
from bluebottle.files.models import RelatedImage
from bluebottle.files.serializers import ImageSerializer, ImageField

from bluebottle.fsm.serializers import (
    AvailableTransitionsField, TransitionSerializer
)

from bluebottle.funding.models import MoneyContribution
from bluebottle.funding.states import FundingStateMachine

from bluebottle.geo.models import Location
from bluebottle.geo.serializers import TinyPointSerializer
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings, Theme
from bluebottle.members.models import Member
from bluebottle.organizations.models import Organization, OrganizationContact

from bluebottle.time_based.models import TimeContribution
from bluebottle.time_based.states import TimeBasedStateMachine

from bluebottle.utils.exchange_rates import convert
from bluebottle.utils.fields import (
    SafeField,
    ValidationErrorsField,
    RequiredErrorsField,
    FSMField
)
from bluebottle.utils.serializers import (
    ResourcePermissionField, NoCommitMixin, AnonymizedResourceRelatedField
)


class ThemeSerializer(ModelSerializer):

    class Meta(object):
        model = Theme
        fields = ('id', 'slug', 'name', 'description')

    class JSONAPIMeta(object):
        resource_name = 'themes'


class CategorySerializer(ModelSerializer):
    image = OldImageSerializer(required=False)
    image_logo = OldImageSerializer(required=False)
    slug = serializers.CharField(read_only=True)

    class Meta(object):
        model = Category
        fields = ('id', 'title', 'slug', 'description', 'image', 'image_logo')

    class JSONAPIMeta(object):
        resource_name = 'categories'


class BaseMemberSerializer(ModelSerializer):
    avatar = SorlImageField('133x133', source='picture', crop='center')
    full_name = serializers.ReadOnlyField(source='get_full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    short_name = serializers.ReadOnlyField(source='get_short_name', read_only=True)
    is_anonymous = serializers.SerializerMethodField()

    class Meta(object):
        model = Member
        fields = (
            'id', 'first_name', 'last_name', 'initials', 'avatar',
            'full_name', 'short_name', 'is_active', 'date_joined',
            'about_me', 'is_co_financer', 'is_anonymous'
        )

    def get_is_anonymous(self, obj):
        return False

    class JSONAPIMeta(object):
        resource_name = 'members'


class MemberSerializer(ModelSerializer):
    avatar = SorlImageField('133x133', source='picture', crop='center')
    full_name = serializers.ReadOnlyField(source='get_full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    short_name = serializers.ReadOnlyField(source='get_short_name', read_only=True)

    class Meta(object):
        model = Member
        fields = (
            'id', 'first_name', 'last_name', 'initials', 'avatar',
            'full_name', 'short_name', 'is_active', 'date_joined',
            'about_me', 'is_co_financer', 'is_anonymous'
        )

    class JSONAPIMeta(object):
        resource_name = 'members'

    def to_representation(self, instance):
        if instance.is_anonymous:
            return {'id': 'anonymous', "is_anonymous": True}

        return BaseMemberSerializer(instance, context=self.context).to_representation(instance)


class InitiativeImageSerializer(ImageSerializer):
    sizes = {
        'preview': '300x168',
        'small': '320x180',
        'large': '600x337',
        'cover': '960x540'
    }
    content_view_name = 'initiative-image'
    relationship = 'initiative_set'


class RelatedInitiativeImageContentSerializer(ImageSerializer):
    sizes = {
        'large': '600',
    }
    content_view_name = 'related-initiative-image-content'
    relationship = 'relatedimage_set'


class InitiativeMapSerializer(serializers.ModelSerializer):
    # Use a standard serializer and tinypoint serializer to keep this request tiny
    # No need to repeat `type` and `latitude`, `longitude` for every record.
    position = TinyPointSerializer()

    class Meta(object):
        model = Initiative
        fields = (
            'id', 'title', 'slug', 'position',
        )


class InitiativeSerializer(NoCommitMixin, ModelSerializer):
    status = FSMField(read_only=True)
    image = ImageField(required=False, allow_null=True)
    owner = AnonymizedResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))
    reviewer = AnonymizedResourceRelatedField(read_only=True)
    promoter = AnonymizedResourceRelatedField(read_only=True)
    activity_manager = AnonymizedResourceRelatedField(read_only=True)
    activities = SerializerMethodResourceRelatedField(
        model=Activity,
        many=True,
        read_only=True
    )
    slug = serializers.CharField(read_only=True)
    story = SafeField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(allow_blank=True)

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    stats = serializers.SerializerMethodField()
    transitions = AvailableTransitionsField(source='states')

    is_open = serializers.ReadOnlyField()

    def get_activities(self, instance):
        user = self.context['request'].user
        activities = [
            activity for activity in instance.activities.all() if
            activity.status != ActivityStateMachine.deleted.value
        ]

        public_statuses = [
            ActivityStateMachine.succeeded.value,
            ActivityStateMachine.open.value,
            TimeBasedStateMachine.full.value,
            FundingStateMachine.partially_funded.value,
        ]

        if user not in (
            instance.owner, instance.activity_manager
        ):
            return [
                activity for activity in activities if (
                    activity.status in public_statuses or
                    user == activity.owner
                )
            ]
        else:
            return activities

    def get_stats(self, obj):
        default_currency = properties.DEFAULT_CURRENCY

        effort = EffortContribution.objects.filter(
            contribution_type='deed',
            status='succeeded',
            contributor__activity__initiative=obj
        ).aggregate(
            count=Count('id', distinct=True),
            activities=Count('contributor__activity', distinct=True)
        )

        time = TimeContribution.objects.filter(
            status='succeeded',
            contributor__activity__initiative=obj
        ).aggregate(
            count=Count('id', distinct=True),
            activities=Count('contributor__activity', distinct=True),
            value=Sum('value')
        )

        money = MoneyContribution.objects.filter(
            status='succeeded',
            contributor__activity__initiative=obj
        ).aggregate(
            count=Count('id', distinct=True),
            activities=Count('contributor__activity', distinct=True)
        )

        amounts = MoneyContribution.objects.filter(
            status='succeeded',
            contributor__activity__initiative=obj
        ).values(
            'value_currency'
        ).annotate(
            amount=Sum('value')
        ).order_by()

        stats = {
            'hours': time['value'].total_seconds() / 3600 if time['value'] else 0,
            'effort': effort['count'],
            'activities': sum(stat['activities'] for stat in [effort, time, money]),
            'contributors': sum(stat['count'] for stat in [effort, time, money]),
        }

        stats['amount'] = {
            'amount': sum(
                convert(
                    Money(c['amount'], c['value_currency']),
                    default_currency
                ).amount
                for c in amounts if c['amount']
            ),
            'currency': default_currency
        }

        return stats

    included_serializers = {
        'categories': 'bluebottle.initiatives.serializers.CategorySerializer',
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'reviewer': 'bluebottle.initiatives.serializers.MemberSerializer',
        'promoter': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity_manager': 'bluebottle.initiatives.serializers.MemberSerializer',
        'place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'location': 'bluebottle.geo.serializers.LocationSerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
        'organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'organization_contact': 'bluebottle.organizations.serializers.OrganizationContactSerializer',
        'activities': 'bluebottle.activities.serializers.ActivityListSerializer',
        'activities.location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'activities.image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'activities.goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'activities.goals.type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'activities.slots': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
        'activities.slots.location': 'bluebottle.geo.serializers.GeolocationSerializer',
    }

    class Meta(object):
        model = Initiative
        fsm_fields = ['status']
        fields = (
            'id', 'title', 'pitch', 'categories',
            'owner', 'reviewer', 'promoter', 'activity_manager',
            'slug', 'has_organization', 'organization',
            'organization_contact', 'story', 'video_url', 'image',
            'theme', 'place', 'location', 'activities',
            'errors', 'required', 'stats', 'is_open',
        )

        meta_fields = (
            'permissions', 'transitions', 'status', 'created', 'required',
            'errors', 'stats',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner', 'reviewer', 'promoter', 'activity_manager',
            'categories', 'theme', 'place', 'location',
            'image', 'organization', 'organization_contact', 'activities',
            'activities.image', 'activities.location',
            'activities.goals', 'activities.goals.type',
            'activities.slots', 'activities.slots.location',
        ]
        resource_name = 'initiatives'


class InitiativeListSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    image = ImageField(required=False, allow_null=True)
    owner = AnonymizedResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))
    activity_manager = AnonymizedResourceRelatedField(read_only=True)
    slug = serializers.CharField(read_only=True)
    story = SafeField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(allow_blank=True)
    transitions = AvailableTransitionsField(source='states')

    included_serializers = {
        'categories': 'bluebottle.initiatives.serializers.CategorySerializer',
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity_manager': 'bluebottle.initiatives.serializers.MemberSerializer',
        'place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'location': 'bluebottle.geo.serializers.LocationSerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
    }

    class Meta(object):
        model = Initiative
        fsm_fields = ['status']
        fields = (
            'id', 'title', 'pitch', 'categories',
            'owner', 'activity_manager',
            'slug', 'has_organization', 'transitions',
            'story', 'image', 'theme', 'place', 'location'
        )

        meta_fields = ('permissions', 'status', 'created', 'transitions',)

    class JSONAPIMeta(object):
        included_resources = [
            'owner', 'activity_manager',
            'categories', 'theme', 'place', 'location',
            'image', 'organization',
        ]
        resource_name = 'initiatives'


def _error_messages_for(label):
    return {
        'error_messages': {'required': "'{}' is required".format(label)}
    }


class RelatedInitiativeImageSerializer(ModelSerializer):
    image = ImageField(required=False, allow_null=True)
    resource = ResourceRelatedField(
        queryset=Initiative.objects.all(),
        source='content_object'
    )

    included_serializers = {
        'resource': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'image': 'bluebottle.initiatives.serializers.RelatedInitiativeImageContentSerializer',
    }

    class Meta(object):
        model = RelatedImage
        fields = ('image', 'resource', )

    class JSONAPIMeta(object):
        included_resources = [
            'resource', 'image',
        ]

        resource_name = 'related-initiative-images'


class OrganizationSubmitSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={'blank': _('Name is required')})

    def __init__(self, *args, **kwargs):
        super(OrganizationSubmitSerializer, self).__init__(*args, **kwargs)

    def validate_empty_values(self, data):
        if self.parent.initial_data['has_organization'] and not data:
            return (False, data)
        else:
            return (False if data else True, data)

    class Meta(object):
        model = Organization
        fields = ('name', )


class OrganizationContactSubmitSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, error_messages={'blank': _('Name is required')})
    email = serializers.CharField(required=True, error_messages={'blank': _('Email is required')})

    def validate_empty_values(self, data):
        if self.parent.initial_data['has_organization'] and not data:
            return (False, data)
        else:
            return (False if data else True, data)

    class Meta(object):
        model = OrganizationContact
        fields = ('name', 'email', 'phone', )


class InitiativeReviewTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Initiative.objects.all())
    field = 'states'
    included_serializers = {
        'resource': 'bluebottle.initiatives.serializers.InitiativeSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource']
        resource_name = 'initiative-transitions'


class InitiativePlatformSettingsSerializer(serializers.ModelSerializer):
    has_locations = serializers.SerializerMethodField()

    def get_has_locations(self, obj):
        return Location.objects.count()

    class Meta(object):
        model = InitiativePlatformSettings

        fields = (
            'activity_types',
            'initiative_search_filters',
            'activity_search_filters',
            'require_organization',
            'contact_method',
            'enable_impact',
            'enable_office_regions',
            'enable_multiple_dates',
            'enable_participant_exports',
            'has_locations'
        )


class InitiativeRedirectSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    route = serializers.CharField()
    params = serializers.DictField()
    target_route = serializers.CharField(read_only=True)
    target_params = serializers.ListField(read_only=True)

    class JSONAPIMeta(object):
        resource_name = 'initiative-redirects'
