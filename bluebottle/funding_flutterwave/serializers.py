from rest_framework import serializers

from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_flutterwave.models import FlutterwavePayment


class FlutterwavePaymentSerializer(PaymentSerializer):
    tx_ref = serializers.CharField(required=True)

    class Meta(PaymentSerializer.Meta):
        model = FlutterwavePayment
        fields = PaymentSerializer.Meta.fields + ('tx_ref', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/flutterwave-payments'
