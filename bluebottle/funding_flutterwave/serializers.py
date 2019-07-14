from rest_framework import serializers
from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_flutterwave.models import FlutterwavePayment
from bluebottle.funding_flutterwave.utils import check_payment_status


class FlutterwavePaymentSerializer(PaymentSerializer):
    tx_ref = serializers.CharField(required=True)

    class Meta(PaymentSerializer.Meta):
        model = FlutterwavePayment
        fields = PaymentSerializer.Meta.fields + ('tx_ref', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/payment-methods'

    def create(self, validated_data):
        payment = super(FlutterwavePaymentSerializer, self).create(validated_data)
        payment = check_payment_status(payment)
        return payment
