from rest_framework import serializers

from bluebottle.bluebottle_drf2.serializers import ObjectFieldSerializer
from bluebottle.payments.models import OrderPayment, OrderPaymentAction


class OrderPaymentActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderPaymentAction
        fields = ('type', 'method', 'url', 'payload')


class ManageOrderPaymentSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(read_only=True,
                                      max_digits=10,
                                      decimal_places=3)
    authorization_action = OrderPaymentActionSerializer(read_only=True)
    payment_method = serializers.CharField(required=True)
    integration_data = ObjectFieldSerializer()

    class Meta:
        model = OrderPayment
        fields = ('id', 'order', 'payment_method', 'integration_data',
                  'amount', 'status', 'authorization_action')
