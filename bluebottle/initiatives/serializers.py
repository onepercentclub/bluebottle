import hashlib
from builtins import object

from django.db.models import Q
from django.urls.base import reverse
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework_json_api.relations import (
    ResourceRelatedField, SerializerMethodResourceRelatedField, HyperlinkedRelatedField
)
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivityListSerializer
from bluebottle.activities.states import ActivityStateMachine
from bluebottle.activities.utils import get_stats_for_activities
from bluebottle.bluebottle_drf2.serializers import (
    ImageSerializer as OldImageSerializer
)
from bluebottle.categories.models import Category
from bluebottle.files.models import RelatedImage
from bluebottle.files.serializers import ImageSerializer, ImageField
from bluebottle.fsm.serializers import (
    AvailableTransitionsField, TransitionSerializer, CurrentStatusField
)
from bluebottle.funding.states import FundingStateMachine
from bluebottle.funding_stripe.models import StripePayoutAccount
from bluebottle.geo.models import Location
from bluebottle.geo.serializers import TinyPointSerializer
from bluebottle.initiatives.models import Initiative, InitiativePlatformSettings, Theme, ActivitySearchFilter, \
    InitiativeSearchFilter
from bluebottle.members.models import Member
from bluebottle.members.serializers import UserPermissionsSerializer
from bluebottle.organizations.models import Organization, OrganizationContact
from bluebottle.segments.models import Segment
from bluebottle.time_based.states import TimeBasedStateMachine
from bluebottle.utils.fields import (
    SafeField,
    ValidationErrorsField,
    RequiredErrorsField,
    FSMField
)
from bluebottle.utils.serializers import (
    ResourcePermissionField, NoCommitMixin
)
from bluebottle.utils.utils import get_current_language


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


class AvatarImageSerializer(ImageSerializer):
    sizes = {
        "avatar": "200x200",
    }
    content_view_name = 'avatar-image'
    relationship = 'member_set'


class MemberSerializer(ModelSerializer):
    full_name = serializers.ReadOnlyField(source='get_full_name', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    short_name = serializers.ReadOnlyField(source='get_short_name', read_only=True)

    avatar = ImageField(required=False, allow_null=True)

    class Meta(object):
        model = Member
        fields = (
            'id', 'first_name', 'last_name', 'initials',
            'full_name', 'short_name', 'is_active', 'date_joined',
            'about_me', 'is_co_financer', 'is_anonymous', 'avatar'
        )

    class JSONAPIMeta(object):
        resource_name = 'members'
        included_resources = ['avatar']

    included_serializers = {
        'avatar': 'bluebottle.initiatives.serializers.AvatarImageSerializer',
    }

    def to_representation(self, instance):
        user = self.context['request'].user
        if instance.is_anonymous:
            return {'id': 'anonymous', "is_anonymous": True}

        representation = super().to_representation(instance)

        if (
            self.context.get('display_member_names') == 'first_name' and
            instance not in self.context.get('owners', []) and
            not user.is_staff and
            not user.is_superuser
        ):
            representation['last_name'] = None
            representation['full_name'] = representation['first_name']

        return representation


class ProfileLinkField(HyperlinkedRelatedField):
    model = Member

    def __init__(self, *args, **kwargs):
        super().__init__(*args, source='*', read_only=True, **kwargs)

    def get_url(self, rel, link_view_name, self_kwargs, request):
        return reverse(self.related_link_view_name, args=(self_kwargs['pk'], ))


class CurrentMemberSerializer(MemberSerializer):
    permissions = UserPermissionsSerializer(read_only=True)
    profile = ProfileLinkField(
        related_link_view_name="member-profile-detail",
    )
    segments = ResourceRelatedField(many=True, read_only=True)
    has_initiatives = serializers.SerializerMethodField()
    can_pledge = serializers.BooleanField(read_only=True)
    can_do_bank_transfer = serializers.BooleanField(read_only=True)

    payout_account = SerializerMethodResourceRelatedField(
        model=StripePayoutAccount,
        many=False,
        read_only=True,
    )

    def get_payout_account(self, obj):
        return StripePayoutAccount.objects.filter(owner=obj).first()

    def get_has_initiatives(self, obj):
        return obj.is_initiator

    class Meta(MemberSerializer.Meta):
        fields = MemberSerializer.Meta.fields + (
            "hours_spent",
            "hours_planned",
            "has_initiatives",
            "segments",
            "has_initiatives",
            "profile",
            "can_pledge",
            "can_do_bank_transfer",
            "payout_account",
        )
        meta_fields = ('permissions', )

    class JSONAPIMeta:
        resource_name = 'members'
        included_resources = MemberSerializer.JSONAPIMeta.included_resources + [
            'segments',

        ]

    included_serializers = dict(
        **MemberSerializer.included_serializers,
        segments='bluebottle.segments.serializers.SegmentDetailSerializer',
    )


class InitiativeImageSerializer(ImageSerializer):
    sizes = {
        "email": "200x200",
        "preview": "300x168",
        "small": "320x180",
        "large": "600x337",
        "cover": "960x540",
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


IMAGE_SIZES = {
    'preview': '300x168',
    'small': '320x180',
    'large': '600x337',
    'cover': '960x540'
}


class InitiativePreviewSerializer(ModelSerializer):
    image = serializers.SerializerMethodField()
    theme = serializers.SerializerMethodField()
    activity_count = serializers.SerializerMethodField()
    current_status = CurrentStatusField(source='states.current_state')

    def get_image(self, obj):
        if obj.image:
            hash = hashlib.md5(obj.image.file.encode('utf-8')).hexdigest()
            url = reverse('initiative-image', args=(obj.image.id, IMAGE_SIZES['large'], ))

            return f'{url}?_={hash}'

    def get_activity_count(self, obj):
        return {
            'total': obj.succeeded_activities_count + obj.open_activities_count,
            'succeeded': obj.succeeded_activities_count,
            'open': obj.open_activities_count
        }

    def get_theme(self, obj):
        try:
            return [
                theme.name
                for theme in obj.theme or []
                if theme.language == get_current_language()
            ][0]
        except IndexError:
            pass

    class Meta(object):
        model = Initiative
        fields = (
            'id', 'title', 'slug', 'image', 'story', 'pitch', 'theme', 'status', 'activity_count'
        )
        meta_fields = ('current_status',)

    class JSONAPIMeta(object):
        resource_name = 'initiatives/preview'


class ActivitiesField(HyperlinkedRelatedField):
    def __init__(self, many=True, read_only=True, *args, **kwargs):
        super().__init__(Activity, many=many, read_only=read_only, *args, **kwargs)

    def get_url(self, name, view_name, kwargs, request):
        return f"{self.reverse('activity-preview-list')}?filter[initiative.id]={kwargs['pk']}&page[size]=1000"


class InitiativeSerializer(NoCommitMixin, ModelSerializer):
    status = FSMField(read_only=True)
    image = ImageField(required=False, allow_null=True)
    owner = ResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))
    activity_managers = ResourceRelatedField(read_only=True, many=True)
    reviewer = ResourceRelatedField(read_only=True)
    promoter = ResourceRelatedField(read_only=True)
    current_status = CurrentStatusField(source='states.current_state')

    activities = ActivitiesField()

    segments = SerializerMethodResourceRelatedField(
        ActivityListSerializer,
        model=Segment,
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
        activities = instance.activities.exclude(status='deleted').all()

        public_statuses = [
            ActivityStateMachine.succeeded.value,
            ActivityStateMachine.open.value,
            TimeBasedStateMachine.full.value,
            FundingStateMachine.partially_funded.value,
        ]

        if user != instance.owner and user not in instance.activity_managers.all():
            if not user.is_authenticated:
                return activities.filter(status__in=public_statuses).exclude(segments__closed=True)
            elif user.is_staff:
                return activities.filter(
                    Q(status__in=public_statuses) |
                    Q(owner=user) |
                    Q(initiative__activity_managers=user)
                )
            else:
                return activities.filter(
                    Q(status__in=public_statuses) |
                    Q(owner=user) |
                    Q(initiative__activity_managers=user)
                ).filter(
                    ~Q(segments__closed=True) |
                    Q(segments__in=user.segments.filter(closed=True))
                )

        return activities

    def get_segments(self, instance):
        segments = []
        for activity in self.get_activities(instance):
            for segment in activity.segments.all():
                if segment not in segments:
                    segments.append(segment)
        return segments

    def get_stats(self, obj):
        return get_stats_for_activities(obj.activities)

    included_serializers = {
        'categories': 'bluebottle.initiatives.serializers.CategorySerializer',
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'owner.avatar': 'bluebottle.initiatives.serializers.AvatarImageSerializer',
        'reviewer': 'bluebottle.initiatives.serializers.MemberSerializer',
        'promoter': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity_managers': 'bluebottle.initiatives.serializers.MemberSerializer',
        'place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
        'organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'organization_contact': 'bluebottle.organizations.serializers.OrganizationContactSerializer',
        'segments': 'bluebottle.segments.serializers.SegmentListSerializer',
        'segments.segment_type': 'bluebottle.segments.serializers.SegmentTypeSerializer',
        'activities': 'bluebottle.activities.serializers.ActivityListSerializer',
        'activities.location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'activities.image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'activities.goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'activities.goals.type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'activities.slots': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
        'activities.slots.location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'activities.collect_type': 'bluebottle.collect.serializers.CollectTypeSerializer',
    }

    class Meta(object):
        model = Initiative
        fsm_fields = ['status']
        fields = (
            'id', 'title', 'pitch', 'categories',
            'owner', 'reviewer', 'promoter', 'activity_managers',
            'slug', 'has_organization', 'organization',
            'organization_contact', 'story', 'video_url', 'image',
            'theme', 'place', 'activities', 'segments',
            'errors', 'required', 'stats', 'is_open', 'status', 'is_global',
        )

        meta_fields = (
            'permissions', 'transitions', 'status', 'created', 'required',
            'errors', 'stats', 'current_status'
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner', 'owner.avatar', 'reviewer', 'promoter', 'activity_managers',
            'categories', 'theme', 'place',
            'image', 'organization', 'organization_contact', 'activities',
            'activities.image', 'activities.location',
            'activities.goals', 'activities.goals.type',
            'activities.slots', 'activities.slots.location',
            'activities.collect_type',
            'segments', 'segments.segment_type'
        ]
        resource_name = 'initiatives'


class InitiativeListSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    image = ImageField(required=False, allow_null=True)
    owner = ResourceRelatedField(read_only=True)
    permissions = ResourcePermissionField('initiative-detail', view_args=('pk',))
    activity_managers = ResourceRelatedField(read_only=True, many=True)
    slug = serializers.CharField(read_only=True)
    story = SafeField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(allow_blank=True)
    transitions = AvailableTransitionsField(source='states')
    current_status = CurrentStatusField(source='states.current_state')

    included_serializers = {
        'categories': 'bluebottle.initiatives.serializers.CategorySerializer',
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity_managers': 'bluebottle.initiatives.serializers.MemberSerializer',
        'place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'theme': 'bluebottle.initiatives.serializers.ThemeSerializer',
    }

    class Meta(object):
        model = Initiative
        fsm_fields = ['status']
        fields = (
            'id', 'title', 'pitch', 'categories',
            'owner', 'activity_managers',
            'slug', 'has_organization', 'transitions',
            'story', 'image', 'theme', 'place',
        )

        meta_fields = ('permissions', 'status', 'current_status', 'created', 'transitions',)

    class JSONAPIMeta(object):
        included_resources = [
            'owner', 'activity_managers',
            'categories', 'theme', 'place',
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


class ActivitySearchFilterSerializer(serializers.ModelSerializer):

    class Meta:
        model = ActivitySearchFilter
        fields = ['type', 'name', 'highlight', 'placeholder']


class InitiativeSearchFilterSerializer(serializers.ModelSerializer):

    class Meta:
        model = InitiativeSearchFilter
        fields = ['type', 'name', 'highlight', 'placeholder']


class InitiativePlatformSettingsSerializer(serializers.ModelSerializer):
    has_locations = serializers.SerializerMethodField()

    search_filters_activities = ActivitySearchFilterSerializer(many=True)
    search_filters_initiatives = InitiativeSearchFilterSerializer(many=True)

    def get_has_locations(self, obj):
        return Location.objects.count()

    class Meta(object):
        model = InitiativePlatformSettings

        fields = (
            'activity_types',
            'initiative_search_filters',
            'activity_search_filters',
            'activity_search_filters',
            'search_filters_activities',
            'search_filters_initiatives',
            'include_full_activities',
            'require_organization',
            'team_activities',
            'contact_method',
            'enable_impact',
            'enable_office_regions',
            'enable_office_restrictions',
            'default_office_restriction',
            'enable_multiple_dates',
            'enable_participant_exports',
            'enable_open_initiatives',
            'has_locations',
            'enable_matching_emails'
        )


class InitiativeRedirectSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    route = serializers.CharField()
    params = serializers.DictField()
    target_route = serializers.CharField(read_only=True)
    target_params = serializers.ListField(read_only=True)

    class JSONAPIMeta(object):
        resource_name = 'initiative-redirects'
