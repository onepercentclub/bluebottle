from rest_framework import serializers
from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_stripe.models import StripePayment


class StripePaymentSerializer(PaymentSerializer):
    intent_id = serializers.CharField(read_only=True)
    client_secret = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = StripePayment
        fields = PaymentSerializer.Meta.fields + ('intent_id', 'client_secret', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/stripe-payments'
