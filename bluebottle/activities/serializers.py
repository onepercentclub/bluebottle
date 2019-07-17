from rest_framework_json_api.serializers import PolymorphicModelSerializer

from bluebottle.activities.models import Contribution, Activity
from bluebottle.events.serializers import EventSerializer, ParticipantSerializer
from bluebottle.funding.serializers import FundingSerializer, DonationSerializer
from bluebottle.assignments.serializers import AssignmentSerializer, AssignmentParticipantSerializer


class ActivitySerializer(PolymorphicModelSerializer):

    polymorphic_serializers = [
        EventSerializer,
        FundingSerializer,
        AssignmentSerializer
    ]

    included_serializers = {
        'contributions': 'bluebottle.events.serializers.ParticipantSerializer',
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
