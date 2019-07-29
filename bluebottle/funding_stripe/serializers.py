from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.funding.models import Donation
from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_stripe.models import (
    StripePayment, ConnectAccount, ExternalAccount
)
from bluebottle.funding_stripe.models import StripeSourcePayment, PaymentIntent


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


class StripeSourcePaymentSerializer(PaymentSerializer):
    charge_token = serializers.CharField(required=False, allow_blank=True)

    class Meta(PaymentSerializer.Meta):
        model = StripeSourcePayment
        fields = PaymentSerializer.Meta.fields + ('source_token', 'charge_token', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-source-payments'


class ExternalAccountSerializer(serializers.ModelSerializer):
    connect_account = ResourceRelatedField(queryset=ConnectAccount.objects.all())
    token = serializers.CharField(write_only=True)

    account_holder_name = serializers.CharField(read_only=True, source='account.account_holder_name')
    country = serializers.CharField(read_only=True, source='account.country')
    last4 = serializers.CharField(read_only=True, source='account.last4')
    currency = serializers.CharField(read_only=True, source='account.currency')
    routing_number = serializers.CharField(read_only=True, source='account.routing_number')

    included_serializers = {
        'connect_account': 'bluebottle.funding_stripe.serializers.ConnectAccountSerializer',
    }

    class Meta:
        model = ExternalAccount

        fields = (
            'id', 'token', 'connect_account', 'account_holder_name',
            'country', 'last4', 'currency', 'routing_number'
        )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/stripe/external-accounts'
        included_resources = ['connect-account']


class ConnectAccountSerializer(serializers.ModelSerializer):
    owner = ResourceRelatedField(read_only=True)
    token = serializers.CharField(write_only=True, required=False, allow_blank=True)

    external_accounts = ResourceRelatedField(read_only=True, many=True)

    included_serializers = {
        'external_accounts': 'bluebottle.funding_stripe.serializers.ExternalAccountSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta:
        model = ConnectAccount

        fields = (
            'id', 'token', 'country',
            'verified', 'owner',
            'required', 'disabled',
            'individual', 'external_accounts',
            'tos_acceptance'
        )

    class JSONAPIMeta():
        resource_name = 'payout-accounts/stripe/connect-accounts'

        included_resources = ['external_accounts', 'owner']
