import re
from rest_framework import serializers

from bluebottle.donations.models import Donation
from bluebottle.projects.models import Project
from bluebottle.utils.serializers import MoneySerializer, MoneyTotalSerializer


class PayoutDonationSerializer(serializers.ModelSerializer):

    amount = MoneySerializer()
    status = serializers.CharField(source='order.status')
    confirmed = serializers.CharField(source='order.confirmed')
    completed = serializers.CharField(source='order.completed')
    type = serializers.CharField(source='order.order_type')

    payment_method = serializers.SerializerMethodField(source='order.order_payment.payment_method')

    def get_payment_method(self, instance):
        return re.sub('([A-Z]+)', r'-\1', instance.order.order_payment.payment_method).lower()

    class Meta:
        model = Donation
        fields = ('id', 'type',
                  'amount', 'status',
                  'confirmed', 'completed',
                  'payment_method')


class ProjectPayoutSerializer(serializers.ModelSerializer):
    amount_asked = MoneySerializer(required=False)
    amount_donated = MoneyTotalSerializer(source='totals_donated', required=False)

    title = serializers.CharField(required=False)
    receiver_account_name = serializers.CharField(source='account_holder_name', required=False)
    receiver_account_number = serializers.CharField(source='account_number', required=False)
    receiver_account_bic = serializers.CharField(source='account_bic', required=False)
    receiver_account_city = serializers.CharField(source='account_holder_city', required=False)
    receiver_account_country = serializers.CharField(source='account_holder_country.name', required=False)

    donations = PayoutDonationSerializer(many=True, required=False)

    class Meta:
        model = Project
        fields = ('id',
                  'payout_status',
                  'title',
                  'amount_donated',
                  'amount_asked',
                  'campaign_started',
                  'campaign_ended',
                  'receiver_account_number',
                  'receiver_account_bic',
                  'receiver_account_name',
                  'receiver_account_city',
                  'receiver_account_country',
                  'donations'
                  )
