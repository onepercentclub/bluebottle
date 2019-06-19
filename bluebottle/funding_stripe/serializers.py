from rest_framework import serializers

from rest_framework_json_api.relations import ResourceRelatedField

from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_stripe.models import StripePayment, StripeKYCCheck


class StripePaymentSerializer(PaymentSerializer):
    intent_id = serializers.CharField(read_only=True)
    client_secret = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = StripePayment
        fields = PaymentSerializer.Meta.fields + ('intent_id', 'client_secret', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-payments'


class StripeKYCCheckSerializer(serializers.ModelSerializer):
    owner = ResourceRelatedField(read_only=True)
    token = serializers.CharField(write_only=True)

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
