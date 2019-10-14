from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField
)
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import (
    ModelSerializer, ValidationError, IntegerField,
    PolymorphicModelSerializer
)

from bluebottle.activities.utils import (
    BaseActivitySerializer, BaseContributionSerializer
)
from bluebottle.files.serializers import ImageField, PrivateDocumentSerializer
from bluebottle.files.serializers import PrivateDocumentField
from bluebottle.funding.filters import DonationListFilter
from bluebottle.funding.models import (
    Funding, Donation, Fundraiser, Reward, BudgetLine, PaymentMethod,
    BankAccount, PayoutAccount, PaymentProvider,
    Payout)
from bluebottle.funding.models import PlainPayoutAccount
from bluebottle.funding_flutterwave.serializers import FlutterwaveBankAccountSerializer
from bluebottle.funding_lipisha.serializers import LipishaBankAccountSerializer
from bluebottle.funding_stripe.serializers import ExternalAccountSerializer, ConnectAccountSerializer
from bluebottle.funding_vitepay.serializers import VitepayBankAccountSerializer
from bluebottle.members.models import Member
from bluebottle.transitions.serializers import TransitionSerializer
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField, FSMField
from bluebottle.utils.serializers import (
    MoneySerializer, FilteredRelatedField, ResourcePermissionField, NoCommitMixin,
)


class FundingCurrencyValidator(object):
    """
    Validates that the currency of the field is the same as the activity currency
    """
    message = _('Currency does not match any of the activities currencies')

    def __init__(self, fields=None, message=None):
        if fields is None:
            fields = ['amount']

        self.fields = fields
        self.message = message or self.message

    def __call__(self, data):
        for field in self.fields:
            if data[field].currency != data['activity'].target.currency:
                raise ValidationError(self.message)


class FundraiserSerializer(ModelSerializer):
    """
    Serializer to view/create fundraisers
    """
    owner = ResourceRelatedField(read_only=True)
    activity = ResourceRelatedField(queryset=Funding.objects.all())
    image = ImageField(required=False, allow_null=True)

    amount = MoneySerializer()
    amount_donated = MoneySerializer(read_only=True)

    validators = [FundingCurrencyValidator()]

    included_serializers = {
        'image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class Meta:
        model = Fundraiser
        fields = (
            'id',
            'owner',
            'activity',
            'title',
            'description',
            'image',
            'amount',
            'amount_donated',
            'deadline'
        )

    class JSONAPIMeta:
        included_resources = [
            'image',
            'owner',
            'activity',
        ]

        resource_name = 'activities/fundraisers'

    def validate(self, data):
        if data.get('deadline') and data['deadline'] > data['activity'].deadline:
            raise ValidationError(
                {'deadline': [_("Fundraiser deadline exceeds activity deadline.")]}
            )
        return data


class RewardSerializer(ModelSerializer):
    activity = ResourceRelatedField(queryset=Funding.objects.all())
    count = IntegerField(read_only=True)
    amount = MoneySerializer(min_amount=5.00)

    validators = [FundingCurrencyValidator()]

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class Meta:
        model = Reward
        fields = ('id', 'title', 'description', 'amount', 'limit', 'activity', 'count')

    class JSONAPIMeta:
        included_resources = [
            'activity',
        ]

        resource_name = 'activities/rewards'


class BudgetLineSerializer(ModelSerializer):
    activity = ResourceRelatedField(queryset=Funding.objects.all())
    amount = MoneySerializer()

    validators = [FundingCurrencyValidator()]

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class Meta:
        model = BudgetLine
        fields = ('activity', 'amount', 'description')

    class JSONAPIMeta:
        included_resources = [
            'activity',
        ]

        resource_name = 'activities/budget-lines'


class PaymentMethodSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    currencies = serializers.SerializerMethodField()
    countries = serializers.ListField()

    class Meta():
        model = PaymentMethod
        fields = ('code', 'name', 'currencies', 'countries', 'activity')

    class JSONAPIMeta:
        resource_name = 'payments/payment-methods'

    def get_currencies(self, obj):
        # Only return payment method currencies that are enabled in back office
        currencies = []
        for enabled_currencies in PaymentProvider.get_currency_choices():
            if enabled_currencies[0] in obj.currencies:
                currencies.append(enabled_currencies[0])
        return currencies


class FundingListSerializer(BaseActivitySerializer):
    permissions = ResourcePermissionField('funding-detail', view_args=('pk',))
    target = MoneySerializer(required=False, allow_null=True)
    amount_raised = MoneySerializer(read_only=True)
    amount_donated = MoneySerializer(read_only=True)
    amount_matching = MoneySerializer(read_only=True)

    class Meta(BaseActivitySerializer.Meta):
        model = Funding
        fields = BaseActivitySerializer.Meta.fields + (
            'country',
            'deadline',
            'duration',
            'target',
            'amount_donated',
            'amount_matching',
            'amount_raised',
            'permissions',
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = [
            'owner',
            'initiative',
            'initiative.image',
            'initiative.location',
            'initiative.place',
        ]
        resource_name = 'activities/fundings'

    included_serializers = {
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'initiative': 'bluebottle.initiatives.serializers.InitiativeSerializer',
        'initiative.image': 'bluebottle.initiatives.serializers.InitiativeImageSerializer',
        'location': 'bluebottle.geo.serializers.GeolocationSerializer',
    }


class BankAccountSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        ExternalAccountSerializer,
        FlutterwaveBankAccountSerializer,
        LipishaBankAccountSerializer,
        VitepayBankAccountSerializer
    ]

    class Meta:
        model = BankAccount

    class JSONAPIMeta:
        included_resources = [
            'owner',
        ]
        resource_name = 'payout-accounts/external-accounts'


class FundingSerializer(NoCommitMixin, FundingListSerializer):
    rewards = RewardSerializer(many=True, required=False)
    budget_lines = BudgetLineSerializer(many=True, required=False)
    payment_methods = PaymentMethodSerializer(many=True, read_only=True)
    contributions = FilteredRelatedField(many=True, filter_backend=DonationListFilter)

    bank_account = PolymorphicResourceRelatedField(
        BankAccountSerializer,
        queryset=BankAccount.objects.all(),
        required=False,
        allow_null=True
    )

    def get_fields(self):
        fields = super(FundingSerializer, self).get_fields()

        if not self.context['request'].user in [
            self.instance.initiative.owner,
            self.instance.initiative.activity_manager
        ]:
            del fields['bank_account']

        return fields

    class Meta(FundingListSerializer.Meta):
        fields = FundingListSerializer.Meta.fields + (
            'rewards',
            'payment_methods',
            'budget_lines',
            'fundraisers',
            'rewards',
            'contributions',
            'bank_account'
        )

    class JSONAPIMeta(FundingListSerializer.JSONAPIMeta):
        included_resources = FundingListSerializer.JSONAPIMeta.included_resources + [
            'rewards',
            'payment_methods',
            'budget_lines',
            'contributions',
            'contributions.user',
            'bank_account',
        ]

    included_serializers = dict(
        FundingListSerializer.included_serializers,
        **{
            'rewards': 'bluebottle.funding.serializers.BudgetLineSerializer',
            'budget_lines': 'bluebottle.funding.serializers.RewardSerializer',
            'payment_methods': 'bluebottle.funding.serializers.PaymentMethodSerializer',
            'contributions': 'bluebottle.funding.serializers.DonationSerializer',
            'bank_account': 'bluebottle.funding.serializers.BankAccountSerializer',
        }
    )


class PayoutSerializer(ModelSerializer):
    donations = FilteredRelatedField(many=True, filter_backend=DonationListFilter)

    class Meta():
        fields = (
            'donations',
        )
        model = Payout

    class JSONAPIMeta():
        included_resources = [
            'donations',
        ]
        resource_name = 'activities/funding-payouts'

    included_serializers = {
        'donations': 'bluebottle.funding.serializers.DonationSerializer',
    }


class FundingPayoutsSerializer(NoCommitMixin, FundingListSerializer):
    bank_account = PolymorphicResourceRelatedField(
        BankAccountSerializer,
        queryset=BankAccount.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta(FundingListSerializer.Meta):
        fields = (
            'payouts',
            'bank_account',
        )

    class JSONAPIMeta:
        included_resources = [
            'payouts',
            'bank_account',
        ]

    included_serializers = {
        'payouts': 'bluebottle.funding.serializers.PayoutSerializer',
        'bank_account': 'bluebottle.funding.serializers.BankAccountSerializer',
    }


class FundingTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Funding.objects.all())
    field = 'transitions'
    included_serializers = {
        'resource': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class JSONAPIMeta:
        included_resources = ['resource', ]
        resource_name = 'funding-transitions'


class IsRelatedToActivity(object):
    """
    Validates that the reward activity is the same as the donation activity
    """
    message = _('The selected reward is not related to this activity')

    def __init__(self, field):
        self.field = field

    def __call__(self, data):
        if data.get(self.field) and not data[self.field].activity == data['activity']:
            raise ValidationError(self.message)


def reward_amount_matches(data):
    """
    Validates that the reward activity is the same as the donation activity
    """
    if data.get('reward') and data['reward'].amount > data['amount']:
        raise ValidationError(
            _('The amount must be higher or equal to the amount of the reward.')
        )


class DonationMemberValidator(object):
    """
    Validates that the reward activity is the same as the donation activity
    """
    message = _('User can only be set, not changed.')

    def set_context(self, serializer):
        if serializer.instance:
            self.user = serializer.instance.user
        else:
            self.user = None

    def __call__(self, data):
        if data.get('user') and data['user'].is_authenticated and self.user and self.user != data['user']:
            raise ValidationError(self.message)


class DonationSerializer(BaseContributionSerializer):
    amount = MoneySerializer()

    user = ResourceRelatedField(
        queryset=Member.objects.all(),
        default=serializers.CurrentUserDefault(),
        allow_null=True,
        required=False
    )

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
        'reward': 'bluebottle.funding.serializers.RewardSerializer',
        'fundraiser': 'bluebottle.funding.serializers.FundraiserSerializer',
    }

    validators = [
        IsRelatedToActivity('reward'),
        IsRelatedToActivity('fundraiser'),
        DonationMemberValidator(),
        reward_amount_matches,
    ]

    class Meta(BaseContributionSerializer.Meta):
        model = Donation
        fields = BaseContributionSerializer.Meta.fields + ('amount', 'fundraiser', 'reward', 'anonymous',)

    class JSONAPIMeta(BaseContributionSerializer.JSONAPIMeta):
        resource_name = 'contributions/donations'
        included_resources = [
            'user',
            'activity',
            'reward',
            'fundraiser',
        ]

    def get_fields(self):
        """
        If the donation is anonymous, we do not return the user.
        """
        fields = super(DonationSerializer, self).get_fields()
        if isinstance(self.instance, Donation) and self.instance.anonymous:
            del fields['user']

        return fields


class DonationCreateSerializer(DonationSerializer):
    amount = MoneySerializer()

    class Meta(DonationSerializer.Meta):
        model = Donation
        fields = DonationSerializer.Meta.fields + ('client_secret', )


class KycDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'kyc-document'
    relationship = 'plainpayoutaccount_set'


class PlainPayoutAccountSerializer(serializers.ModelSerializer):
    document = PrivateDocumentField(required=False, allow_null=True, permissions=[IsAdminUser])
    owner = ResourceRelatedField(read_only=True)
    status = FSMField(read_only=True)
    external_accounts = PolymorphicResourceRelatedField(
        BankAccountSerializer,
        read_only=True,
        many=True
    )

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'external_accounts': 'bluebottle.funding.serializers.BankAccountSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
        'document': 'bluebottle.funding.serializers.KycDocumentSerializer',
    }

    class Meta:
        model = PlainPayoutAccount

        fields = (
            'id',
            'owner',
            'status',
            'document',
            'required',
            'errors',
            'external_accounts'
        )
        meta_fields = ('required', 'errors', 'status')

    class JSONAPIMeta():
        resource_name = 'payout-accounts/plains'
        included_resources = [
            'external_accounts',
            'owner',
            'document',
        ]


class PayoutAccountSerializer(PolymorphicModelSerializer):

    external_accounts = PolymorphicResourceRelatedField(
        BankAccountSerializer,
        read_only=True,
        many=True
    )

    polymorphic_serializers = [
        PlainPayoutAccountSerializer,
        ConnectAccountSerializer,
    ]

    class Meta:
        model = PayoutAccount
        fields = (
            'id',
            'owner',
            'status',
            'required',
            'errors',
        )
        meta_fields = ('required', 'errors', 'required_fields', 'status',)

    class JSONAPIMeta():
        resource_name = 'payout-accounts/account'
        included_resources = [
            'external_accounts',
            'owner',
        ]

    included_serializers = {
        'external_accounts': 'bluebottle.funding.serializers.BankAccountSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }
