from rest_framework_json_api.relations import PolymorphicResourceRelatedField
from rest_framework_json_api.serializers import PolymorphicModelSerializer, ModelSerializer

from bluebottle.activities.models import Contribution, Activity
from bluebottle.assignments.serializers import AssignmentListSerializer, AssignmentSerializer, \
    TinyApplicantSerializer
from bluebottle.events.serializers import EventListSerializer, EventSerializer, \
    TinyParticipantSerializer
from bluebottle.files.models import RelatedImage
from bluebottle.files.serializers import ImageSerializer, ImageField
from bluebottle.funding.serializers import FundingListSerializer, FundingSerializer, \
    TinyDonationSerializer
from bluebottle.transitions.serializers import TransitionSerializer


class ActivityListSerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        EventListSerializer,
        FundingListSerializer,
        AssignmentListSerializer
    ]

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
        'initiative.place': 'bluebottle.geo.serializers.GeolocationSerializer',
    }

    class Meta:
        model = Activity
        meta_fields = (
            'permissions',
            'transitions', 'review_transitions',
            'created', 'updated',
        )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
            'location',
            'initiative.image',
            'initiative.place',
            'initiative.location',
        ]


class ActivitySerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        EventSerializer,
        FundingSerializer,
        AssignmentSerializer
    ]

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'initiative.location': 'bluebottle.geo.serializers.LocationSerializer',
        'initiative.place': 'bluebottle.geo.serializers.GeolocationSerializer',
        'initiative.organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'initiative.organization_contact': 'bluebottle.organizations.serializers.OrganizationContactSerializer',
    }

    class Meta:
        model = Activity
        meta_fields = (
            'permissions',
            'transitions', 'review_transitions',
            'created', 'updated',
            'errors', 'required',
        )

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
            'location',
            'initiative.image',
            'initiative.place',
            'initiative.location',
            'initiative.organization',
            'initiative.organization_contact',
        ]


class TinyActivityListSerializer(ModelSerializer):
    class Meta:
        model = Activity
        fields = ('id', 'slug', 'title', )
        meta_fields = (
            'created', 'updated',
        )


class ContributionSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        TinyParticipantSerializer,
        TinyApplicantSerializer,
        TinyDonationSerializer
    ]

    included_serializers = {
        'activity': 'bluebottle.activities.serializers.TinyActivityListSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class JSONAPIMeta:
        included_resources = [
            'user',
            'activity',
        ]

    class Meta:
        meta_fields = ('permissions', 'transitions', 'created', 'updated', )
        model = Contribution


class ActivityReviewTransitionSerializer(TransitionSerializer):
    resource = PolymorphicResourceRelatedField(ActivitySerializer, queryset=Activity.objects.all())
    field = 'review_transitions'
    included_serializers = {
        'resource': 'bluebottle.activities.serializers.ActivitySerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource']
        resource_name = 'activities/review-transitions'


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

    class Meta:
        model = RelatedImage
        fields = ('image', 'resource', )

    class JSONAPIMeta:
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
