from rest_framework import serializers

from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_stripe.models import (
    StripePayment, StripeKYCCheck, ExternalAccount
)


class StripePaymentSerializer(PaymentSerializer):
    intent_id = serializers.CharField(read_only=True)
    client_secret = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = StripePayment
        fields = PaymentSerializer.Meta.fields + ('intent_id', 'client_secret', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-payments'


class ExternalAccountSerializer(serializers.ModelSerializer):
    stripe_kyc_check = ResourceRelatedField(queryset=StripeKYCCheck.objects.all())
    token = serializers.CharField(write_only=True)

    account_holder_name = serializers.CharField(read_only=True, source='account.account_holder_name')
    country = serializers.CharField(read_only=True, source='account.country')
    last4 = serializers.CharField(read_only=True, source='account.last4')
    currency = serializers.CharField(read_only=True, source='account.currency')
    routing_number = serializers.CharField(read_only=True, source='account.routing_number')

    included_serializers = {
        'stripe_kyc_check': 'bluebottle.funding_stripe.serializers.StripeKYCCheckSerializer',
    }

    class Meta:
        model = ExternalAccount

        fields = (
            'id', 'token', 'stripe_kyc_check', 'account_holder_name',
            'country', 'last4', 'currency', 'routing_number'
        )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'kyc-check/stripe-external-accounts'
        included_resources = ['stripe_kyc_check']


class StripeKYCCheckSerializer(serializers.ModelSerializer):
    owner = ResourceRelatedField(read_only=True)
    token = serializers.CharField(write_only=True)

    external_accounts = ResourceRelatedField(read_only=True, many=True)

    included_serializers = {
        'external_accounts': 'bluebottle.funding_stripe.serializers.ExternalAccountSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta:
        model = StripeKYCCheck

        fields = (
            'id', 'token', 'country',
            'verified', 'owner',
            'required', 'disabled',
            'personal_data', 'external_accounts',
        )

    class JSONAPIMeta():
        resource_name = 'kyc-check/stripe'

        included_resources = ['external_accounts', 'owner']
