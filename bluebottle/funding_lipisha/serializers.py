from rest_framework import serializers

from bluebottle.funding.serializers import PaymentSerializer
from bluebottle.funding_lipisha.models import LipishaPayment


class LipishaPaymentSerializer(PaymentSerializer):
    transaction = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = LipishaPayment
        fields = PaymentSerializer.Meta.fields + ('mobile_number', 'transaction')

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/lipisha-payments'
