from builtins import object

from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField
from rest_framework_json_api.serializers import ModelSerializer


from bluebottle.fsm.serializers import CurrentStatusField
from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding.models import Donor
from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount,
    ExternalAccount)
from bluebottle.funding_stripe.models import StripeSourcePayment, PaymentIntent
from bluebottle.funding_stripe.utils import get_stripe


class PaymentIntentSerializer(ModelSerializer):
    intent_id = serializers.CharField(read_only=True)
    client_secret = serializers.CharField(read_only=True)

    donation = ResourceRelatedField(queryset=Donor.objects.all())

    class Meta(object):
        model = PaymentIntent
        fields = ('intent_id', 'client_secret', 'donation')

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-payment-intents'
        included_resources = ['donation', 'donation.activity', 'donation.updates']

    included_serializers = {
        'donation': 'bluebottle.funding.serializers.DonorSerializer',
        'donation.updates': 'bluebottle.updates.serializers.UpdateSerializer',
        'donation.activity': 'bluebottle.funding.serializers.FundingSerializer',
    }


class BankTransferSerializer(PaymentIntentSerializer):
    intent_id = serializers.CharField(read_only=True)
    client_secret = serializers.CharField(read_only=True)
    next_url = serializers.SerializerMethodField()

    def get_next_url(self, obj):
        return obj.instructions.display_bank_transfer_instructions.hosted_instructions_url

    donation = ResourceRelatedField(queryset=Donor.objects.all())

    class Meta(object):
        model = PaymentIntent
        fields = ('intent_id', 'client_secret', 'donation', 'next_url')

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-bank-transfers'
        included_resources = ['donation', 'donation.activity', 'donation.updates']

    included_serializers = {
        'donation': 'bluebottle.funding.serializers.DonorSerializer',
        'donation.updates': 'bluebottle.updates.serializers.UpdateSerializer',
        'donation.activity': 'bluebottle.funding.serializers.FundingSerializer',
    }


class StripePaymentSerializer(PaymentSerializer):
    payment_intent = ResourceRelatedField(queryset=PaymentIntent.objects.all(), write_only=True)

    class Meta(PaymentSerializer.Meta):
        model = StripePayment
        fields = PaymentSerializer.Meta.fields + ('payment_intent', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-payments'


class ConnectAccountSerializer(ModelSerializer):
    current_status = CurrentStatusField(source='states.current_state')
    owner = ResourceRelatedField(read_only=True)
    external_accounts = ResourceRelatedField(read_only=True, many=True)

    included_serializers = {
        'external_accounts': 'bluebottle.funding_stripe.serializers.ExternalAccountSerializer',
        'partner_organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(object):
        model = StripePayoutAccount

        fields = (
            "id",
            "account_id",
            "owner",
            "country",
            "verified",
            "payments_enabled",
            "payouts_enabled",
            "external_accounts",
            "partner_organization",
            "country",
            "current_status",
            "business_type",
            "tos_accepted",
        )
        meta_fields = ('current_status',)

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/stripes'
        included_resources = [
            'external_accounts',
            'owner',
            'partner_organization'
        ]


class ConnectAccountSessionSerializer(serializers.Serializer):
    client_secret = serializers.CharField()
    account_id = serializers.CharField(source="account")

    class Meta(object):
        fields = ("id", "account_id", "client_secret")

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/stripe-sessions'


class StripeSourcePaymentSerializer(PaymentSerializer):
    charge_token = serializers.CharField(required=False, allow_blank=True)

    class Meta(PaymentSerializer.Meta):
        model = StripeSourcePayment
        fields = PaymentSerializer.Meta.fields + ('source_token', 'charge_token', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-source-payments'


class ExternalAccountSerializer(BaseBankAccountSerializer):
    connect_account = ResourceRelatedField(queryset=StripePayoutAccount.objects.all())
    token = serializers.CharField(write_only=True)

    account_name = serializers.CharField(read_only=True, source='connect_account.name')
    account_holder_name = serializers.CharField(read_only=True, source='account.account_holder_name')
    country = serializers.CharField(read_only=True, source='account.country')
    last4 = serializers.CharField(read_only=True, source='account.last4')
    currency = serializers.CharField(read_only=True, source='account.currency')
    routing_number = serializers.CharField(read_only=True, source='account.routing_number')
    account_id = serializers.CharField(read_only=True)
    bank_name = serializers.CharField(read_only=True, source='account.bank_name')

    included_serializers = {
        'connect_account': 'bluebottle.funding_stripe.serializers.ConnectAccountSerializer',
        'connect_account.partner_organization': 'bluebottle.organizations.serializers.OrganizationSerializer',
    }

    def create(self, data):
        stripe = get_stripe()
        account = stripe.Account.create_external_account(
            data["connect_account"].account_id, external_account=data.pop("token")
        )
        data["account_id"] = account.id

        return super().create(data)

    class Meta(BaseBankAccountSerializer.Meta):
        model = ExternalAccount

        fields = BaseBankAccountSerializer.Meta.fields + (
            'token',
            'account_id',
            'account_holder_name',
            'country',
            'last4',
            'currency',
            'routing_number',
            'bank_name',
            'account_name'
        )

    class JSONAPIMeta(BaseBankAccountSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/stripe-external-accounts'
        included_resources = ['connect_account', 'connect_account.partner_organization']


class PayoutStripeBankSerializer(ModelSerializer):
    account_id = serializers.CharField(source='connect_account.account_id')
    external_account_id = serializers.CharField(source='account_id')
    currency = serializers.CharField(read_only=True, source='account.currency')

    class Meta(object):
        fields = (
            'id',
            'account_id',
            'external_account_id',
            'currency'
        )
        model = ExternalAccount


class CountrySpecSerializer(serializers.Serializer):
    default_currency = serializers.CharField()
    supported_bank_account_currencies = serializers.ListField(child=serializers.CharField())
    supported_payment_currencies = serializers.ListField(child=serializers.CharField())
    supported_payment_methods = serializers.ListField(child=serializers.CharField())
    supported_transfer_countries = serializers.ListField(child=serializers.CharField())
    verification_fields = serializers.SerializerMethodField()

    def get_verification_fields(self, obj):
        return (
            obj.verification_fields.individual.minimum
            + obj.verification_fields.individual.additional
        )

    class Meta(object):
        fields = (
            "id",
            "default_currency",
            "supported_bank_account_currencies",
            "supported_payment_currencies",
            "supported_payments_methods",
            "supported_transfer_countries",
            "verification_fields",
        )
        model = ExternalAccount

    class JSONAPIMeta:
        resource_name = "country-specs"
