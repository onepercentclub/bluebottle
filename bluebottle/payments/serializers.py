from rest_framework import serializers

from bluebottle.payments.models import OrderPayment, OrderPaymentAction
from bluebottle.utils.serializers import MoneySerializer


class OrderPaymentActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPaymentAction
        fields = ('type', 'method', 'url', 'payload')


class ManageOrderPaymentSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    amount = MoneySerializer(read_only=True)
    authorization_action = OrderPaymentActionSerializer(read_only=True)
    payment_method = serializers.CharField(required=True)
    integration_data = serializers.JSONField()

    class Meta:
        model = OrderPayment
        fields = ('id', 'order', 'payment_method', 'integration_data',
                  'amount', 'status', 'authorization_action')
