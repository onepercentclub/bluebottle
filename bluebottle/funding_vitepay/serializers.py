from rest_framework import serializers
from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_stripe.models import StripePayment


class VitepayPaymentSerializer(PaymentSerializer):
    mobile_number = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = StripePayment
        fields = PaymentSerializer.Meta.fields + ('mobile_number',)

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/vitepay-payments'
