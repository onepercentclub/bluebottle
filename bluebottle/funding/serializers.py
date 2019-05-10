from bluebottle.activities.serializers import BaseActivitySerializer, ContributionSerializer
from bluebottle.funding.models import Funding, Donation
from bluebottle.utils.serializers import MoneySerializer


class FundingSerializer(BaseActivitySerializer):
    target = MoneySerializer()
    amount_donated = MoneySerializer()

    class Meta:
        model = Funding
        fields = BaseActivitySerializer.Meta.fields + (
            'deadline', 'duration', 'target' 'amount_donated',
        )


class DonationSerializer(ContributionSerializer):
    amount = MoneySerializer()

    class Meta:
        model = Donation
        fields = ContributionSerializer.Meta.fields + ('amount', )
