from rest_framework import serializers

from bluebottle.donations.serializers import ManageDonationSerializer
from bluebottle.orders.models import Order
from bluebottle.members.models import Member
from bluebottle.utils.serializers import MoneySerializer


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'created')


class ManageOrderSerializer(serializers.ModelSerializer):
    total = MoneySerializer(read_only=True)
    status = serializers.ChoiceField(choices=Order.STATUS_CHOICES, read_only=True)
    user = serializers.PrimaryKeyRelatedField(queryset=Member.objects, required=False, allow_null=True)
    donations = ManageDonationSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'total', 'status',
                  'donations', 'created', 'payment_message')
