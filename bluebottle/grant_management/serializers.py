from builtins import object
from rest_framework import serializers
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField,
    ResourceRelatedField,
)
from rest_framework_json_api.serializers import (
    ModelSerializer,
)

from bluebottle.activities.utils import (
    BaseActivityListSerializer,
    BaseActivitySerializer,
    BaseContributorSerializer,
)
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.funding.models import BankAccount
from bluebottle.funding.serializers import BankAccountSerializer
from bluebottle.funding_stripe.models import StripePayoutAccount
from bluebottle.grant_management.models import (
    GrantApplication, GrantDonor, GrantFund, GrantPayout,
)
from bluebottle.utils.fields import RichTextField
from bluebottle.utils.serializers import MoneySerializer, ResourcePermissionField


class GrantApplicationTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=GrantApplication.objects.all())
    included_serializers = {
        'resource': 'bluebottle.funding.serializers.GrantApplicationSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/grant-application-transitions'


class PayoutGrantSerializer(ModelSerializer):
    # For Payout service
    amount = MoneySerializer()
    fund = ResourceRelatedField(read_only=True)

    class Meta(object):
        fields = (
            'id',
            'amount',
            'fund',
            'status',
        )
        model = GrantDonor
        included_resources = [
            'fund',
        ]

    included_serializers = {
        'fund': 'bluebottle.funding.serializers.PayoutGrantFundSerializer'
    }


class PayoutGrantFundSerializer(ModelSerializer):

    class Meta(object):
        fields = (
            'id',
            'name',
        )
        model = GrantFund


class PayoutGrantApplicationSerializer(BaseActivityListSerializer):

    class Meta(BaseActivityListSerializer.Meta):
        model = GrantApplication
        fields = (
            'title', 'bank_account',
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/grant-applications'
        included_resources = [
            'bank_account'
        ]

    included_serializers = {
        'bank_account': 'bluebottle.funding.serializers.PayoutBankAccountSerializer'
    }


class GrantPayoutSerializer(ModelSerializer):
    # For Payout service
    activity = ResourceRelatedField(read_only=True)
    currency = serializers.CharField(read_only=True)
    status = serializers.CharField(write_only=True)
    method = serializers.CharField(source='provider', read_only=True)
    donations = ResourceRelatedField(source='grants', read_only=True, many=True)

    class Meta(object):
        fields = (
            'id',
            'status',
            'activity',
            'method',
            'currency',
            'donations'
        )
        model = GrantPayout

    class JSONAPIMeta(object):
        resource_name = 'funding/grant-payouts'
        included_resources = [
            'activity',
            'donations',
            'donations.fund',
            'activity.bank_account'
        ]

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.PayoutGrantApplicationSerializer',
        'activity.bank_account': 'bluebottle.funding.serializers.PayoutBankAccountSerializer',
        'donations': 'bluebottle.funding.serializers.PayoutGrantSerializer',
        'donations.fund': 'bluebottle.funding.serializers.PayoutGrantFundSerializer'
    }


class GrantFundSerializer(ModelSerializer):
    description = RichTextField()

    class Meta:
        model = GrantFund
        fields = ['name', 'description']

    class JSONAPIMeta:
        resource_name = 'activities/grant-funds'


class GrantSerializer(BaseContributorSerializer):
    amount = MoneySerializer()
    fund = ResourceRelatedField(read_only=True)

    class Meta(BaseContributorSerializer.Meta):
        model = GrantDonor
        fields = BaseContributorSerializer.Meta.fields + (
            "amount",
            "fund"
        )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/grants'

    included_serializers = {
        'fund': 'bluebottle.funding.serializers.GrantFundSerializer',
    }


class GrantApplicationSerializer(BaseActivitySerializer):

    target = MoneySerializer(required=False, allow_null=True)
    permissions = ResourcePermissionField('funding-detail', view_args=('pk',))
    grants = ResourceRelatedField(
        many=True,
        model=GrantDonor,
        read_only=True
    )

    amount_granted = MoneySerializer(read_only=True)

    payout_account = ResourceRelatedField(
        source='bank_account.connect_account',
        model=StripePayoutAccount,
        many=False,
        read_only=True,
    )

    bank_account = PolymorphicResourceRelatedField(
        BankAccountSerializer,
        queryset=BankAccount.objects.all(),
        required=False,
        allow_null=True
    )

    def get_fields(self):
        fields = super(GrantApplicationSerializer, self).get_fields()

        user = self.context["request"].user
        if (
            self.instance
            and user not in self.instance.owners
            and not user.is_staff
            and not user.is_superuser
        ):
            del fields["payout_account"]
            del fields["bank_account"]
            del fields["required"]
            del fields["errors"]
        return fields

    class Meta(BaseActivitySerializer.Meta):
        model = GrantApplication
        fields = BaseActivitySerializer.Meta.fields + (
            "target",
            "grants",
            "amount_granted",
            "bank_account",
            "payout_account",
            "answers",
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/grant-applications'
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'grants',
            'grants.fund',
            'bank_account',
            'payout_account',
            'answers',
            'answers.segment',
            'answers.question'
            'answers.file'

        ]

    included_serializers = dict(
        BaseActivitySerializer.included_serializers.serializers,
        **{
            'payout_account': 'bluebottle.funding_stripe.serializers.ConnectAccountSerializer',
            'bank_account': 'bluebottle.funding.serializers.BankAccountSerializer',
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
            'grants': 'bluebottle.funding.serializers.GrantSerializer',
            'grants.fund': 'bluebottle.funding.serializers.GrantFundSerializer',
            'answers': 'bluebottle.activities.serializers.ActivityAnswerSerializer',
            'answers.segment': 'bluebottle.segments.serializers.SegmentListSerializer',
            'answers.file': 'bluebottle.files.serializers.DocumentSerializer',
            'answers.question': 'bluebottle.activities.serializers.ActivityQuestionSerializer',
        }
    )
