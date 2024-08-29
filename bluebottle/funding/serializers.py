from builtins import object
from datetime import datetime

import pytz
from dateutil.parser import parse
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser


from rest_framework_json_api.relations import (
    HyperlinkedRelatedField,
    PolymorphicResourceRelatedField
)
from rest_framework_json_api.relations import ResourceRelatedField, SerializerMethodResourceRelatedField
from rest_framework_json_api.serializers import (
    ModelSerializer, ValidationError, IntegerField,
    PolymorphicModelSerializer
)

from bluebottle.activities.utils import (
    BaseContributorSerializer, BaseContributorListSerializer,
    BaseActivityListSerializer, BaseActivitySerializer,
    BaseTinyActivitySerializer
)
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.files.serializers import PrivateDocumentField
from bluebottle.files.serializers import PrivateDocumentSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.funding.models import (
    Funding, Donor, Reward, BudgetLine, PaymentMethod,
    BankAccount, PayoutAccount, PaymentProvider,
    Payout, FundingPlatformSettings)
from bluebottle.funding.models import PlainPayoutAccount
from bluebottle.funding.permissions import CanExportSupportersPermission
from bluebottle.funding_flutterwave.serializers import (
    FlutterwaveBankAccountSerializer, PayoutFlutterwaveBankAccountSerializer
)
from bluebottle.funding_lipisha.serializers import (
    LipishaBankAccountSerializer, PayoutLipishaBankAccountSerializer
)
from bluebottle.funding_pledge.serializers import (
    PledgeBankAccountSerializer, PayoutPledgeBankAccountSerializer
)
from bluebottle.funding_stripe.models import StripePayoutAccount
from bluebottle.funding_stripe.serializers import (
    ExternalAccountSerializer, ConnectAccountSerializer, PayoutStripeBankSerializer
)
from bluebottle.funding_telesom.serializers import PayoutTelesomBankAccountSerializer, TelesomBankAccountSerializer
from bluebottle.funding_vitepay.serializers import (
    VitepayBankAccountSerializer, PayoutVitepayBankAccountSerializer
)
from bluebottle.members.models import Member
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField, FSMField
from bluebottle.utils.serializers import (
    MoneySerializer, ResourcePermissionField, )


class FundingCurrencyValidator(object):
    """
    Validates that the currency of the field is the same as the activity currency
    """
    message = _('Currency does not match any of the activities currencies')
    requires_context = True

    def __init__(self, fields=None, message=None):
        if fields is None:
            fields = ['amount']

        self.fields = fields
        self.message = message or self.message

    def __call__(self, data, serializer_field):
        activity = data.get('activity') or serializer_field.instance.activity

        for field in self.fields:
            if (
                activity.target and
                field in data and
                data[field].currency != activity.target.currency
            ):
                raise ValidationError(self.message)


class RewardSerializer(ModelSerializer):
    activity = ResourceRelatedField(queryset=Funding.objects.all())
    count = IntegerField(read_only=True)
    amount = MoneySerializer(min_amount=5.00)
    description = serializers.CharField(required=False)
    validators = [FundingCurrencyValidator()]

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class Meta(object):
        model = Reward
        fields = ('id', 'title', 'description', 'amount', 'limit', 'activity', 'count')

    class JSONAPIMeta(object):
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

    class Meta(object):
        model = BudgetLine
        fields = ('activity', 'amount', 'description')

    class JSONAPIMeta(object):
        included_resources = [
            'activity',
        ]

        resource_name = 'activities/budget-lines'


class PaymentMethodSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    provider = serializers.CharField()
    currencies = serializers.SerializerMethodField()
    countries = serializers.ListField()

    class Meta(object):
        model = PaymentMethod
        fields = ('code', 'name', 'provider', 'currencies', 'countries', 'activity')

    class JSONAPIMeta(object):
        resource_name = 'payments/payment-methods'

    def get_currencies(self, obj):
        # Only return payment method currencies that are enabled in back office
        currencies = []
        for enabled_currencies in PaymentProvider.get_currency_choices():
            if enabled_currencies[0] in obj.currencies:
                currencies.append(enabled_currencies[0])
        return currencies


class BankAccountSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        ExternalAccountSerializer,
        FlutterwaveBankAccountSerializer,
        LipishaBankAccountSerializer,
        VitepayBankAccountSerializer,
        TelesomBankAccountSerializer,
        PledgeBankAccountSerializer
    ]

    class Meta(object):
        model = BankAccount

    class JSONAPIMeta(object):
        included_resources = [
            'owner',
        ]
        resource_name = 'payout-accounts/external-accounts'


class DeadlineField(serializers.DateTimeField):
    def to_internal_value(self, value):
        if not value:
            return None
        try:
            parsed_date = parse(value).date()
            naive_datetime = datetime.combine(parsed_date, datetime.min.time())
            aware_datetime = pytz.timezone('UTC').localize(naive_datetime)
            return aware_datetime
        except (ValueError, TypeError):
            self.fail('invalid', format='date')


class FundingListSerializer(BaseActivityListSerializer):
    target = MoneySerializer(required=False, allow_null=True)
    permissions = ResourcePermissionField('funding-detail', view_args=('pk',))
    amount_raised = MoneySerializer(read_only=True)
    amount_donated = MoneySerializer(read_only=True)
    amount_matching = MoneySerializer(read_only=True)

    deadline = DeadlineField(required=False, allow_null=True)

    class Meta(BaseActivityListSerializer.Meta):
        model = Funding
        fields = BaseActivityListSerializer.Meta.fields + (
            'country',
            'deadline',
            'duration',
            'target',
            'amount_donated',
            'amount_matching',
            'amount_raised',
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/fundings'

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'location': 'bluebottle.geo.serializers.GeolocationSerializer',
        }
    )


class TinyFundingSerializer(BaseTinyActivitySerializer):

    class Meta(BaseTinyActivitySerializer.Meta):
        model = Funding
        fields = BaseTinyActivitySerializer.Meta.fields + ('target', )

    class JSONAPIMeta(BaseTinyActivitySerializer.JSONAPIMeta):
        resource_name = 'activities/fundings'


class PKHyperlinkRelatedSerializer(HyperlinkedRelatedField):

    def __init__(self, url_name, model, **kwargs):
        self.url_name = url_name
        self.model = model

        super(PKHyperlinkRelatedSerializer, self).__init__(
            source="parent", read_only=True, **kwargs
        )

    def get_links(self, obj, field_name):
        return {"related": reverse(self.url_name, args=(getattr(obj, field_name),))}


class FundingSerializer(BaseActivitySerializer):
    target = MoneySerializer(required=False, allow_null=True)
    amount_raised = MoneySerializer(read_only=True)
    amount_donated = MoneySerializer(read_only=True)
    amount_matching = MoneySerializer(read_only=True)
    rewards = ResourceRelatedField(
        many=True, read_only=True
    )
    budget_lines = ResourceRelatedField(
        many=True, read_only=True
    )
    payment_methods = SerializerMethodResourceRelatedField(
        read_only=True, many=True, source='get_payment_methods', model=PaymentMethod
    )
    permissions = ResourcePermissionField('funding-detail', view_args=('pk',))

    connect_account = PKHyperlinkRelatedSerializer(
        url_name="connect-account-detail", model=StripePayoutAccount, many=False
    )

    bank_account = PolymorphicResourceRelatedField(
        BankAccountSerializer,
        queryset=BankAccount.objects.all(),
        required=False,
        allow_null=True
    )

    supporters_export_url = PrivateFileSerializer(
        'funding-supporters-export', url_args=('pk', ),
        filename='supporters.csv',
        permission=CanExportSupportersPermission,
        read_only=True
    )
    co_financers = SerializerMethodResourceRelatedField(
        read_only=True, many=True, model=Donor
    )

    account_info = serializers.DictField(source='bank_account.public_data', read_only=True)

    psp = serializers.SerializerMethodField()
    deadline = DeadlineField(allow_null=True, required=False)

    def get_psp(self, obj):
        if obj.bank_account and obj.bank_account.connect_account:
            return obj.bank_account.provider

    def get_connect_account(self, obj):
        __import__("ipdb").set_trace()

    def get_fields(self):
        fields = super(FundingSerializer, self).get_fields()

        user = self.context['request'].user
        if user not in [
            self.instance.owner,
            self.instance.initiative.owner,
        ] and user not in self.instance.initiative.activity_managers.all():
            del fields['bank_account']
            del fields['required']
            del fields['errors']
        return fields

    def get_co_financers(self, instance):
        return instance.contributors.instance_of(Donor).\
            filter(user__is_co_financer=True, status='succeeded').all()

    class Meta(BaseActivitySerializer.Meta):
        model = Funding
        fields = BaseActivitySerializer.Meta.fields + (
            "country",
            "deadline",
            "duration",
            "target",
            "amount_donated",
            "amount_matching",
            "amount_raised",
            "account_info",
            "co_financers",
            "rewards",
            "payment_methods",
            "budget_lines",
            "bank_account",
            "connect_account",
            "supporters_export_url",
            "psp",
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'payment_methods',
            'rewards',
            'budget_lines',
            'bank_account',
            'co_financers',
            'co_financers.user',
        ]
        resource_name = 'activities/fundings'

    included_serializers = dict(
        BaseActivitySerializer.included_serializers,
        **{
            'co_financers': 'bluebottle.funding.serializers.DonorSerializer',
            'rewards': 'bluebottle.funding.serializers.RewardSerializer',
            'budget_lines': 'bluebottle.funding.serializers.BudgetLineSerializer',
            'bank_account': 'bluebottle.funding.serializers.BankAccountSerializer',
            'payment_methods': 'bluebottle.funding.serializers.PaymentMethodSerializer',
        }
    )

    def get_payment_methods(self, obj):
        if not obj.bank_account:
            return []

        methods = obj.bank_account.payment_methods

        request = self.context['request']

        if request.user.is_authenticated and request.user.can_pledge:
            methods.append(
                PaymentMethod(
                    provider='pledge',
                    code='pledge',
                    name=_('Pledge'),
                    currencies=[
                        'EUR', 'USD', 'NGN', 'UGX', 'KES', 'XOF', 'BGN'
                    ]
                )
            )

        return methods


class FundingTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Funding.objects.all())
    included_serializers = {
        'resource': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class JSONAPIMeta(object):
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


class DonorMemberValidator(object):
    """
    Validates that the reward activity is the same as the donation activity
    """
    message = _('User can only be set, not changed.')

    requires_context = True

    def __call__(self, data, serializer_field):

        if serializer_field.instance:
            user = serializer_field.instance.user
        else:
            user = None

        if data.get('user') and data['user'].is_authenticated and user and user != data['user']:
            raise ValidationError(self.message)


class DonorListSerializer(BaseContributorListSerializer):
    amount = MoneySerializer()
    payout_amount = MoneySerializer()

    user = ResourceRelatedField(
        queryset=Member.objects.all(),
        default=serializers.CurrentUserDefault(),
        allow_null=True,
        required=False
    )

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.TinyFundingSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(BaseContributorListSerializer.Meta):
        model = Donor
        fields = BaseContributorListSerializer.Meta.fields + ('amount', 'payout_amount', 'name', 'reward', 'anonymous',)
        meta_fields = ('created', 'updated', )

    class JSONAPIMeta(BaseContributorListSerializer.JSONAPIMeta):
        resource_name = 'contributors/donations'
        included_resources = [
            'user',
            'activity',
        ]


class DonorSerializer(BaseContributorSerializer):
    amount = MoneySerializer()
    payout_amount = MoneySerializer(read_only=True)

    payment_methods = SerializerMethodResourceRelatedField(
        read_only=True, many=True, source='get_payment_methods', model=PaymentMethod
    )
    updates = ResourceRelatedField(read_only=True, many=True)

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
        'updates': 'bluebottle.updates.serializers.UpdateSerializer',
        'payment_methods': 'bluebottle.funding.serializers.PaymentMethodSerializer',
    }

    validators = [
        IsRelatedToActivity('reward'),
        DonorMemberValidator(),
        reward_amount_matches,
    ]

    class Meta(BaseContributorSerializer.Meta):
        model = Donor
        fields = BaseContributorSerializer.Meta.fields + (
            'amount', 'payout_amount', 'name', 'reward', 'anonymous', 'payment_methods', 'updates'
        )

    class JSONAPIMeta(BaseContributorSerializer.JSONAPIMeta):
        resource_name = 'contributors/donations'
        included_resources = [
            'user',
            'activity',
            'reward',
            'payment_methods',
            'payment_intent'
        ]

    def get_payment_methods(self, obj):
        if not obj.activity.bank_account:
            return []

        methods = [
            method for method in obj.activity.bank_account.payment_methods
            if str(obj.amount.currency) in method.currencies
        ]

        request = self.context['request']

        if request.user.is_authenticated and request.user.can_pledge:
            methods.append(
                PaymentMethod(
                    provider='pledge',
                    code='pledge',
                    name=_('Pledge'),
                    currencies=[str(obj.amount.currency)]
                )
            )

        return methods

    def get_fields(self):
        """
        If the donor is anonymous, we do not return the user.
        """
        fields = super(DonorSerializer, self).get_fields()
        funding_settings = FundingPlatformSettings.load()
        if isinstance(self.instance, Donor) and (
            self.instance.anonymous or
            funding_settings.anonymous_donations
        ):
            del fields['user']
        return fields


class DonorCreateSerializer(DonorSerializer):
    amount = MoneySerializer()

    class Meta(DonorSerializer.Meta):
        model = Donor
        fields = DonorSerializer.Meta.fields + ('client_secret',)


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

    class Meta(object):
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

    class JSONAPIMeta(object):
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

    class Meta(object):
        model = PayoutAccount
        fields = (
            'id',
            'owner',
            'status',
            'required',
            'errors',
        )
        meta_fields = ('required', 'errors', 'required_fields', 'status',)

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/account'
        included_resources = [
            'external_accounts',
            'owner',
        ]

    included_serializers = {
        'external_accounts': 'bluebottle.funding.serializers.BankAccountSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }


class PayoutBankAccountSerializer(PolymorphicModelSerializer):
    polymorphic_serializers = [
        PayoutStripeBankSerializer,
        PayoutFlutterwaveBankAccountSerializer,
        PayoutLipishaBankAccountSerializer,
        PayoutVitepayBankAccountSerializer,
        PayoutTelesomBankAccountSerializer,
        PayoutPledgeBankAccountSerializer
    ]

    # For Payout service
    class Meta(object):
        model = BankAccount


class PayoutDonationSerializer(serializers.ModelSerializer):
    # For Payout service
    amount = MoneySerializer(source='payout_amount')

    class Meta(object):
        fields = (
            'id',
            'amount',
            'status'
        )
        model = Donor


class PayoutFundingSerializer(BaseActivityListSerializer):

    class Meta(BaseActivityListSerializer.Meta):
        model = Funding
        fields = (
            'title', 'bank_account',
        )

    class JSONAPIMeta(BaseActivityListSerializer.JSONAPIMeta):
        resource_name = 'activities/fundings'
        included_resources = [
            'bank_account'
        ]

    included_serializers = {
        'bank_account': 'bluebottle.funding.serializers.PayoutBankAccountSerializer'
    }


class PayoutSerializer(serializers.ModelSerializer):
    # For Payout service
    donations = ResourceRelatedField(read_only=True, many=True)
    activity = ResourceRelatedField(read_only=True)
    currency = serializers.CharField(read_only=True)
    status = serializers.CharField(write_only=True)
    method = serializers.CharField(source='provider', read_only=True)

    class Meta(object):
        fields = (
            'id',
            'status',
            'activity',
            'method',
            'currency',
            'donations',
        )
        model = Payout

    class JSONAPIMeta(object):
        resource_name = 'funding/payouts'
        included_resources = [
            'activity',
            'donations',
            'activity.bank_account'
        ]

    included_serializers = {
        'activity': 'bluebottle.funding.serializers.PayoutFundingSerializer',
        'activity.bank_account': 'bluebottle.funding.serializers.PayoutBankAccountSerializer',
        'donations': 'bluebottle.funding.serializers.PayoutDonationSerializer'
    }


class FundingPlatformSettingsSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = FundingPlatformSettings

        fields = (
            'allow_anonymous_rewards',
            'anonymous_donations',
            'stripe_publishable_key'
        )
