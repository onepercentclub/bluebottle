from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.funding.models import Donation
from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount,
    ExternalAccount)
from bluebottle.funding_stripe.models import StripeSourcePayment, PaymentIntent
from bluebottle.utils.fields import ValidationErrorsField, RequiredErrorsField


class PaymentIntentSerializer(serializers.ModelSerializer):
    intent_id = serializers.CharField(read_only=True)
    client_secret = serializers.CharField(read_only=True)

    donation = ResourceRelatedField(queryset=Donation.objects.all())

    included_serializers = {
        'donation': 'bluebottle.funding.serializers.DonationSerializer',
    }

    class Meta(object):
        model = PaymentIntent
        fields = ('intent_id', 'client_secret', 'donation')

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-payment-intents'


class StripePaymentSerializer(PaymentSerializer):
    payment_intent = ResourceRelatedField(queryset=PaymentIntent.objects.all(), write_only=True)

    class Meta(PaymentSerializer.Meta):
        model = StripePayment
        fields = PaymentSerializer.Meta.fields + ('payment_intent', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-payments'


class ConnectAccountSerializer(serializers.ModelSerializer):
    owner = ResourceRelatedField(read_only=True)
    token = serializers.CharField(write_only=True, required=False, allow_blank=True)
    account = serializers.DictField(read_only=True)

    external_accounts = ResourceRelatedField(read_only=True, many=True)

    errors = ValidationErrorsField()
    required = RequiredErrorsField()

    included_serializers = {
        'external_accounts': 'bluebottle.funding_stripe.serializers.ExternalAccountSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta:
        model = StripePayoutAccount

        fields = (
            'id', 'token', 'country', 'document_type',
            'verified', 'owner', 'disabled', 'account',
            'external_accounts', 'required', 'errors',
            'required_fields',
        )
        meta_fields = ('required', 'errors', 'required_fields',)

    class JSONAPIMeta():
        resource_name = 'payout-accounts/stripes'

        included_resources = ['external_accounts', 'owner']


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

    account_holder_name = serializers.CharField(read_only=True, source='account.account_holder_name')
    country = serializers.CharField(read_only=True, source='account.country')
    last4 = serializers.CharField(read_only=True, source='account.last4')
    currency = serializers.CharField(read_only=True, source='account.currency')
    routing_number = serializers.CharField(read_only=True, source='account.routing_number')
    account_id = serializers.CharField(read_only=True)

    included_serializers = {
        'connect_account': 'bluebottle.funding_stripe.serializers.ConnectAccountSerializer',
    }

    class Meta(BaseBankAccountSerializer.Meta):
        model = ExternalAccount

        fields = BaseBankAccountSerializer.Meta.fields + (
            'token',
            'account_id',
            'account_holder_name',
            'country',
            'last4',
            'currency',
            'routing_number'
        )

    class JSONAPIMeta(BaseBankAccountSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/stripe-external-accounts'
        included_resources = ['connect-account']


class PayoutStripeBankSerializer(serializers.ModelSerializer):
    account_id = serializers.CharField(source='connect_account.account_id')
    external_account_id = serializers.CharField(source='account_id')
    currency = serializers.CharField(read_only=True, source='account.currency')

    class Meta:
        fields = (
            'id',
            'account_id',
            'external_account_id',
            'currency'
        )
        model = ExternalAccount
