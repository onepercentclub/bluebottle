from builtins import object
from datetime import datetime, timedelta

from dateutil.parser import parse
from django.db import connection
from django.utils.timezone import get_current_timezone, make_aware, now
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.permissions import IsAdminUser
from rest_framework_json_api.relations import (
    PolymorphicResourceRelatedField,
    ResourceRelatedField,
    SerializerMethodResourceRelatedField,
)
from rest_framework_json_api.serializers import (
    IntegerField,
    ModelSerializer,
    PolymorphicModelSerializer,
    ValidationError,
)

from bluebottle.activities.utils import (
    BaseActivityListSerializer,
    BaseActivitySerializer,
    BaseContributorListSerializer,
    BaseContributorSerializer,
    BaseTinyActivitySerializer,
)
from bluebottle.bluebottle_drf2.serializers import PrivateFileSerializer
from bluebottle.files.serializers import PrivateDocumentField, PrivateDocumentSerializer
from bluebottle.fsm.serializers import TransitionSerializer
from bluebottle.funding.models import (
    BankAccount,
    BudgetLine,
    Donor,
    Funding,
    FundingPlatformSettings,
    PaymentMethod,
    PaymentProvider,
    Payout,
    PayoutAccount,
    PlainPayoutAccount,
    Reward, GrantApplication, GrantDonor, GrantFund, GrantPayout,
)
from bluebottle.funding.permissions import CanExportSupportersPermission
from bluebottle.funding_flutterwave.serializers import (
    FlutterwaveBankAccountSerializer,
    PayoutFlutterwaveBankAccountSerializer,
)
from bluebottle.funding_lipisha.serializers import (
    LipishaBankAccountSerializer,
    PayoutLipishaBankAccountSerializer,
)
from bluebottle.funding_pledge.serializers import (
    PayoutPledgeBankAccountSerializer,
    PledgeBankAccountSerializer,
)
from bluebottle.funding_stripe.models import StripePayoutAccount, StripePaymentProvider
from bluebottle.funding_stripe.serializers import (
    ConnectAccountSerializer,
    ExternalAccountSerializer,
    PayoutStripeBankSerializer,
)
from bluebottle.funding_telesom.serializers import (
    PayoutTelesomBankAccountSerializer,
    TelesomBankAccountSerializer,
)
from bluebottle.funding_vitepay.serializers import (
    PayoutVitepayBankAccountSerializer,
    VitepayBankAccountSerializer,
)
from bluebottle.geo.models import Geolocation
from bluebottle.members.models import Member
from bluebottle.time_based.serializers import RelatedLinkFieldByStatus
from bluebottle.utils.fields import FSMField, RequiredErrorsField, ValidationErrorsField, RichTextField
from bluebottle.utils.serializers import MoneySerializer, ResourcePermissionField


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
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
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

    validators = [
        FundingCurrencyValidator(),
    ]

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
            return make_aware(
                datetime(
                    parsed_date.year,
                    parsed_date.month,
                    parsed_date.day,
                    hour=23,
                    minute=59,
                    second=59
                ),
                get_current_timezone()
            )
        except (ValueError, TypeError):
            self.fail('invalid', format='date')


class MaxDeadlineValidator(object):
    """
    Validates that the reward activity is the same as the donation activity
    """
    message = _('The deadline should not be more then 60 days in the future')

    def __call__(self, data):
        if (
            'deadline' in data and
            data['deadline'] and
            data['deadline'] >= now() + timedelta(days=60)
        ):
            raise ValidationError({'deadline': self.message})


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
        BaseActivitySerializer.included_serializers.serializers,
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


class FundingSerializer(BaseActivitySerializer):
    target = MoneySerializer(required=False, allow_null=True)
    amount_raised = MoneySerializer(read_only=True)
    amount_donated = MoneySerializer(read_only=True)
    amount_matching = MoneySerializer(read_only=True)
    account_currency = serializers.SerializerMethodField()

    impact_location = ResourceRelatedField(
        queryset=Geolocation.objects.all(),
        required=False,
        allow_null=True,
    )

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

    payout_account = ResourceRelatedField(
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
    errors = ValidationErrorsField(ignore=["kyc"])

    donations = RelatedLinkFieldByStatus(
        read_only=True,
        related_link_view_name="activity-donation-list",
        related_link_url_kwarg="activity_id",
        statuses={
            "succeeded": ["succeeded"],
            "pending": ["pending", "new"],
            "failed": ["failed", "refunded", "activity_refunded"],
        },
    )

    validators = [
        MaxDeadlineValidator(),
    ]

    def get_account_currency(self, obj):
        if obj.bank_account and getattr(obj.bank_account, 'account', False):
            if not obj.bank_account.currency:
                obj.bank_account.currency = getattr(obj.bank_account.account, 'currency', None)
                if not obj.bank_account.currency:
                    return None
                obj.bank_account.save()
            return obj.bank_account.currency.upper()
        return None

    def get_psp(self, obj):
        if obj.bank_account and obj.bank_account.connect_account:
            return obj.bank_account.provider

    def get_fields(self):
        fields = super(FundingSerializer, self).get_fields()

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
            'account_currency',
            "account_info",
            "co_financers",
            "rewards",
            "payment_methods",
            "budget_lines",
            "bank_account",
            "payout_account",
            "supporters_export_url",
            "psp",
            "donations",
            "impact_location"
        )

    class JSONAPIMeta(BaseActivitySerializer.JSONAPIMeta):
        included_resources = BaseActivitySerializer.JSONAPIMeta.included_resources + [
            'payment_methods',
            'rewards',
            'budget_lines',
            'bank_account',
            'co_financers',
            'co_financers.user',
            'partner_organization',
            'impact_location'
        ]
        resource_name = 'activities/fundings'

    included_serializers = dict(
        BaseActivitySerializer.included_serializers.serializers,
        **{
            'co_financers': 'bluebottle.funding.serializers.DonorSerializer',
            'rewards': 'bluebottle.funding.serializers.RewardSerializer',
            'budget_lines': 'bluebottle.funding.serializers.BudgetLineSerializer',
            'bank_account': 'bluebottle.funding.serializers.BankAccountSerializer',
            'payment_methods': 'bluebottle.funding.serializers.PaymentMethodSerializer',
            'impact_location': 'bluebottle.geo.serializers.GeolocationSerializer',
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

    def get_partner_organization(self, obj):
        organization = super().get_partner_organization(obj)
        if organization:
            return obj.initiative.organization
        elif (
            obj.bank_account
            and obj.bank_account.connect_account
            and obj.bank_account.connect_account.partner_organization
        ):
            return obj.bank_account.connect_account.partner_organization


class FundingTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=Funding.objects.all())
    included_serializers = {
        'resource': 'bluebottle.funding.serializers.FundingSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'funding-transitions'


class GrantApplicationTransitionSerializer(TransitionSerializer):
    resource = ResourceRelatedField(queryset=GrantApplication.objects.all())
    included_serializers = {
        'resource': 'bluebottle.funding.serializers.GrantApplicationSerializer',
    }

    class JSONAPIMeta(object):
        included_resources = ['resource', ]
        resource_name = 'activities/grant-application-transitions'


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
            {'amount': _('The amount must be higher or equal to the amount of the reward.')}

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
        'activity': 'bluebottle.funding.serializers.FundingSerializer',
        'user': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(BaseContributorListSerializer.Meta):
        model = Donor
        fields = BaseContributorListSerializer.Meta.fields + ('amount', 'payout_amount', 'name', 'reward', 'anonymous',)

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

    def validate_amount(self, value):
        provider = StripePaymentProvider.objects.first()
        currency_code = str(value.currency)
        currency_settings = provider.get_currency_settings(currency_code)

        if currency_settings:
            min_amount = currency_settings.min_amount
            max_amount = currency_settings.max_amount

            if min_amount and value.amount < min_amount:
                raise serializers.ValidationError(
                    _("Amount must be at least {amount} {currency}").format(
                        amount=min_amount, currency=currency_code
                    )
                )

            if max_amount and value.amount > max_amount:
                raise serializers.ValidationError(
                    _("Amount cannot exceed {amount} {currency}").format(
                        amount=max_amount, currency=currency_code
                    )
                )

        return value


class KycDocumentSerializer(PrivateDocumentSerializer):
    content_view_name = 'kyc-document'
    relationship = 'plainpayoutaccount_set'


class PlainPayoutAccountSerializer(ModelSerializer):
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


class PayoutDonationSerializer(ModelSerializer):
    # For Payout service
    amount = MoneySerializer(source='payout_amount')

    class Meta(object):
        fields = (
            'id',
            'amount',
            'status'
        )
        model = Donor


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


class PayoutSerializer(ModelSerializer):
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
        'donations': 'bluebottle.funding.serializers.PayoutDonationSerializer',
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


class FundingPlatformSettingsSerializer(ModelSerializer):
    matching_name = serializers.SerializerMethodField()

    def get_matching_name(self, obj):
        return obj.matching_name or connection.tenant.name

    class Meta(object):
        model = FundingPlatformSettings

        fields = (
            'allow_anonymous_rewards',
            'anonymous_donations',
            'stripe_publishable_key',
            'public_accounts',
            'matching_name'
        )


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
        queryset=GrantDonor.objects.all(),
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
            'answers': 'bluebottle.activities.utils.ActivityAnswerSerializer',
            'answers.segment': 'bluebottle.segments.serializers.SegmentListSerializer',
            'answers.file': 'bluebottle.files.serializers.DocumentSerializer',
            'answers.question': 'bluebottle.activities.serializers.ActivityQuestionSerializer',
        }
    )
