from rest_framework import serializers

from bluebottle.donations.serializers import ManageDonationSerializer
from bluebottle.orders.models import Order
from bluebottle.members.models import Member


class OrderSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True, queryset=Member.objects)

    class Meta:
        model = Order
        fields = ('id', 'user', 'created')


class ManageOrderSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(read_only=True)
    status = serializers.ChoiceField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(required=False, queryset=Member.objects)
    donations = ManageDonationSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'total', 'status', 'donations', 'created')
