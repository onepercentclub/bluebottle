from builtins import object

from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField, ResourceRelatedField
)
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.activities.models import Contributor, Activity, Team
from bluebottle.collect.serializers import CollectActivityListSerializer, CollectActivitySerializer, \
    CollectContributorListSerializer
from bluebottle.deeds.serializers import (
    DeedListSerializer, DeedSerializer, DeedParticipantListSerializer
)
from bluebottle.files.models import RelatedImage
from bluebottle.files.serializers import ImageSerializer, ImageField
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.funding.serializers import (
    FundingListSerializer, FundingSerializer,
    DonorListSerializer, TinyFundingSerializer
)
from bluebottle.time_based.serializers import (
    DateActivityListSerializer,
    PeriodActivityListSerializer,

    DateActivitySerializer,
    PeriodActivitySerializer, DateParticipantSerializer, PeriodParticipantSerializer,
    DateParticipantListSerializer, PeriodParticipantListSerializer,
)


class ActivityImageSerializer(ImageSerializer):
    sizes = {
        'preview': '300x168',
        'small': '320x180',
        'large': '600x337',
        'cover': '960x540'
    }
    content_view_name = 'activity-image'
    relationship = 'activity_set'


class ActivityListSerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        FundingListSerializer,
        DeedListSerializer,
        CollectActivityListSerializer,
        DateActivityListSerializer,
        PeriodActivityListSerializer,
    ]

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
        'initiative.place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'collect_type': 'bluebottle.collect.serializers.CollectTypeSerializer',
    }

    class Meta(object):
        model = Activity
        meta_fields = (
            'permissions',
            'created',
            'updated',
            'matching_properties',
        )

    class JSONAPIMeta(object):
        resource_name = 'activities/activity'
        included_resources = [
            'owner',
            'initiative',
            'location',
            'image',
            'goals',
            'goals.type',
            'initiative.image',
            'initiative.place',
            'initiative.location',
        ]


class ActivitySerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        FundingSerializer,
        DeedSerializer,
        CollectActivitySerializer,
        DateActivitySerializer,
        PeriodActivitySerializer,
    ]

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'goals': 'bluebottle.impact.serializers.ImpactGoalSerializer',
        'goals.type': 'bluebottle.impact.serializers.ImpactTypeSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'image': 'bluebottle.activities.serializers.ActivityImageSerializer',
        'initiative.activity_managers': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative.promoter': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
        'initiative.place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'initiative.organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'initiative.organization_contact': 'bluebottle.organizations.serializers.OrganizationContactSerializer',
    }

    class Meta(object):
        model = Activity
        meta_fields = (
            'permissions',
            'transitions',
            'created',
            'updated',
            'errors',
            'required',
        )

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
            'image',
            'initiative',
            'goals',
            'goals.type',
            'location',
            'initiative.image',
            'initiative.place',
            'initiative.location',
            'initiative.activity_managers',
            'initiative.promoter',
            'initiative.organization',
            'initiative.organization_contact',
        ]


class TinyActivityListSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        TinyFundingSerializer,
        DateActivityListSerializer,
        PeriodActivityListSerializer,
    ]

    class Meta(object):
        model = Activity
        fields = ('id', 'slug', 'title', )
        meta_fields = (
            'created', 'updated',
        )


class ContributorSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DonorListSerializer,
        DateParticipantSerializer,
        PeriodParticipantSerializer
    ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.ActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
        ]

    class Meta(object):
        model = Contributor
        meta_fields = (
            'created', 'updated',
        )


class ContributorListSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        DonorListSerializer,
        DateParticipantListSerializer,
        PeriodParticipantListSerializer,
        DeedParticipantListSerializer,
        CollectContributorListSerializer
    ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.TinyActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'slots': 'bluebottle.time_based.serializers.SlotParticipantSerializer',
        'slots.slot': 'bluebottle.time_based.serializers.DateActivitySlotSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = [
            'user',
            'activity',
            'slots',
            'slots.slot',
        ]

    class Meta(object):
        model = Contributor
        meta_fields = (
            'created', 'updated',
        )


class ActivityTransitionSerializer(TransitionSerializer):
    resource = PolymorphicResourceRelatedField(ActivitySerializer, queryset=Activity.objects.all())
    field = 'states'

    included_serializers = {
        'resource': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource']
        resource_name = 'activities/transitions'


class RelatedActivityImageSerializer(ModelSerializer):
    image = ImageField(required=False, allow_null=True)
    resource = PolymorphicResourceRelatedField(
        ActivitySerializer,
        queryset=Activity.objects.all(),
        source='content_object'
    )

    included_serializers = {
        'resource': 'bluebottle.activities.serializers.ActivitySerializer',
        'image': 'bluebottle.activities.serializers.RelatedActivityImageContentSerializer',
    }

    class Meta(object):
        model = RelatedImage
        fields = ('image', 'resource', )

    class JSONAPIMeta(object):
        included_resources = [
            'resource', 'image',
        ]

        resource_name = 'related-activity-images'


class RelatedActivityImageContentSerializer(ImageSerializer):
    sizes = {
        'large': '600',
    }
    content_view_name = 'related-activity-image-content'
    relationship = 'relatedimage_set'


class TeamTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Team.objects.all())
    field = 'states'

    included_serializers = {
        'resource': 'bluebottle.activities.utils.TeamSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource']
        resource_name = 'activities/team-transitions'
