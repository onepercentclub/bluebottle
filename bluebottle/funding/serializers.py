from bluebottle.activities.utils import BaseContributionSerializer, BaseActivitySerializer
from bluebottle.funding.models import Funding, Donation
from bluebottle.utils.serializers import MoneySerializer


class FundingSerializer(BaseActivitySerializer):
    target = MoneySerializer()

    class Meta:
        model = Funding
        fields = BaseActivitySerializer.Meta.fields + (
            'deadline', 'duration', 'target',
        )


class DonationSerializer(BaseContributionSerializer):
    amount = MoneySerializer()

    class Meta:
        model = Donation
        fields = BaseContributionSerializer.Meta.fields + ('amount', )
