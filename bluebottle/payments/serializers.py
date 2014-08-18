from bluebottle.payments.models import OrderPayment, AuthorizationAction
from rest_framework import serializers


class AuthorizationSerializer(serializers.ModelSerializer):

    class Meta:
        model = AuthorizationAction
        fields = ('type', 'method', 'url', 'payload')


class ManagePaymentSerializer(serializers.ModelSerializer):

    status = serializers.CharField(read_only=True)
    amount = serializers.DecimalField(read_only=True)
    authorization_action = AuthorizationSerializer()

    class Meta:
        model = OrderPayment
        fields = ('id', 'order', 'payment_method', 'payment_meta_data', 'amount', 'status', 'authorization_action')