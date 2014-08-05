# coding=utf-8
from bluebottle.utils.utils import get_serializer_class, get_model_class
from rest_framework import serializers

ORDER_MODEL = get_model_class('ORDERS_ORDER_MODEL')


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ORDER_MODEL
        fields = ('id', 'user', 'created')


class ManageOrderSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(read_only=True)
    status = serializers.ChoiceField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    donations = get_serializer_class('DONATIONS_DONATION_MODEL', 'manage')(many=True, read_only=True)

    class Meta:
        model = ORDER_MODEL
        fields = ('id', 'user', 'total', 'status', 'donations', 'created', 'country')


