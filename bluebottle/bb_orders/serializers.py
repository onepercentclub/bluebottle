from bluebottle.utils.model_dispatcher import get_order_model
from rest_framework import serializers
from bluebottle.utils.serializer_dispatcher import get_serializer_class


ORDER_MODEL = get_order_model()


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ORDER_MODEL
        fields = ('id', 'user', 'created')


class ManageOrderSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(read_only=True)
    status = serializers.ChoiceField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(required=False)
    donations = get_serializer_class('DONATIONS_DONATION_MODEL', 'manage')(many=True, read_only=True)

    class Meta:
        model = ORDER_MODEL
        fields = ('id', 'user', 'total', 'status', 'donations', 'created')
