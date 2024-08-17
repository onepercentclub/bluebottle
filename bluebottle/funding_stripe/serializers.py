from builtins import object

from django.urls import reverse
from rest_framework import serializers
from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.fsm.serializers import CurrentStatusField
from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding.models import Donor
from bluebottle.funding_stripe.models import (
    StripePayment, StripePayoutAccount,
    ExternalAccount)
from bluebottle.funding_stripe.models import StripeSourcePayment, PaymentIntent


class PaymentIntentSerializer(serializers.ModelSerializer):
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


class StripePaymentSerializer(PaymentSerializer):
    payment_intent = ResourceRelatedField(queryset=PaymentIntent.objects.all(), write_only=True)

    class Meta(PaymentSerializer.Meta):
        model = StripePayment
        fields = PaymentSerializer.Meta.fields + ('payment_intent', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-payments'


class ConnectAccountSerializer(serializers.ModelSerializer):
    current_status = CurrentStatusField(source='states.current_state')
    owner = ResourceRelatedField(read_only=True)
    account = serializers.DictField(read_only=True)
    external_accounts = ResourceRelatedField(read_only=True, many=True)
    session_link = serializers.SerializerMethodField()

    def get_session_link(self, obj):
        return reverse('stripe-account-session', kwargs={'pk': obj.id})

    included_serializers = {
        'external_accounts': 'bluebottle.funding_stripe.serializers.ExternalAccountSerializer',
        'owner': 'bluebottle.initiatives.serializers.MemberSerializer',
    }

    class Meta(object):
        model = StripePayoutAccount

        fields = (
            'id', 'account_id', 'country', 'document_type',
            'verified', 'owner', 'disabled', 'account',
            'external_accounts', 'country', 'current_status', 'business_type', 'session_link'
        )
        meta_fields = ('current_status',)

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/stripes'
        included_resources = ['external_accounts', 'owner']


class ConnectAccountSessionSerializer(ConnectAccountSerializer):
    client_secret = serializers.SerializerMethodField()

    def get_client_secret(self, obj):
        return obj.get_client_secret()

    class Meta(object):
        model = StripePayoutAccount

        fields = (
            'id', 'account_id', 'client_secret'
        )

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

    account_holder_name = serializers.CharField(read_only=True, source='account.account_holder_name')
    country = serializers.CharField(read_only=True, source='account.country')
    last4 = serializers.CharField(read_only=True, source='account.last4')
    currency = serializers.CharField(read_only=True, source='account.currency')
    routing_number = serializers.CharField(read_only=True, source='account.routing_number')
    account_id = serializers.CharField(read_only=True)
    bank_name = serializers.CharField(read_only=True, source='account.bank_name')

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
            'routing_number',
            'bank_name'
        )

    class JSONAPIMeta(BaseBankAccountSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/stripe-external-accounts'
        included_resources = ['connect-account']


class PayoutStripeBankSerializer(serializers.ModelSerializer):
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
