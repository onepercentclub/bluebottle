from rest_framework_json_api.serializers import PolymorphicModelSerializer
from rest_framework_json_api.relations import PolymorphicResourceRelatedField

from bluebottle.activities.models import Contribution, Activity
from bluebottle.events.serializers import ParticipantSerializer, EventListSerializer
from bluebottle.funding.serializers import FundingSerializer, DonationSerializer
from bluebottle.assignments.serializers import AssignmentSerializer, AssignmentParticipantSerializer

from bluebottle.transitions.serializers import TransitionSerializer


class ActivitySerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        EventListSerializer,
        FundingSerializer,
        AssignmentSerializer
    ]

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
    }

    class Meta:
        model = Activity

    class JSONAPIMeta:
        included_resources = [
            'owner',
            'initiative',
            'location',
            'initiative.image'
        ]


class ContributionSerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        ParticipantSerializer,
        AssignmentParticipantSerializer,
        DonationSerializer
    ]

    class Meta:
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
