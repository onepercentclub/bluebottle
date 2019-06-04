from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer, ActivitySubmitSerializer
)
from bluebottle.funding.models import Funding, Donation, Payment
from bluebottle.transitions.serializers import AvailableTransitionsField
from bluebottle.utils.fields import FSMField
from bluebottle.utils.serializers import MoneySerializer, ResourcePermissionField
from bluebottle.transitions.serializers import TransitionSerializer


class FundingSerializer(BaseActivitySerializer):
    target = MoneySerializer()

    class Meta:
        model = Funding
        fields = BaseActivitySerializer.Meta.fields + (
            'deadline', 'duration', 'target',
        )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        included_resources = [
            'image',
            'owner',
            'initiative',
            'place'
        ]
        resource_name = 'activities/funding'

    included_serializers = {
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'place': 'bluebottle.geo.serializers.GeolocationSerializer',
    }


class FundingSubmitSerializer(ActivitySubmitSerializer):
    target = MoneySerializer(required=True)

    class Meta(ActivitySubmitSerializer.Meta):
        model = Funding
        fields = ActivitySubmitSerializer.Meta.fields + (
            'target',
        )


class FundingTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Funding.objects.all())
    field = 'status'
    included_serializers = {
        'resource': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', ]
        resource_name = 'funding-transitions'


class DonationSerializer(BaseContributionSerializer):
    amount = MoneySerializer()

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(BaseContributionSerializer.Meta):
        model = Donation
        fields = BaseContributionSerializer.Meta.fields + ('amount', )

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'donations'
        included_resources = [
            'user',
            'activity'
        ]


class PaymentSerializer(ModelSerializer):
    status = FSMField(read_only=True)
    donation = ResourceRelatedField(queryset=Donation.objects.all())

    transitions = AvailableTransitionsField(source='status')

    included_serializers = {
        'donation': 'bluebottle.funding.serializers.DonationSerializer',
    }

    class Meta:
        model = Payment
        fields = ('donation', 'status', )
        meta_fields = ('transitions', 'created', 'updated', )

    class JSONAPIMeta:
        included_resources = [
            'donation',
        ]
        resource_name = 'payments'
