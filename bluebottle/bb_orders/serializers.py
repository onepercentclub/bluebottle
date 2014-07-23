# coding=utf-8
from bluebottle.bluebottle_drf2.serializers import EuroField
from bluebottle.bb_donations.serializers import DonationSerializer, MyDonationSerializer
from django.utils.translation import ugettext as _
from rest_framework import serializers
from .models import Order, OrderStatuses


class OrderSerializer(serializers.ModelSerializer):
    total = serializers.DecimalField(read_only=True)
    status = serializers.ChoiceField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    donations = MyDonationSerializer(source='donations', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'total', 'status', 'donations', 'created')

