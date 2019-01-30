import re
from rest_framework import serializers

from bluebottle.donations.models import Donation
from bluebottle.payouts.serializers import PayoutAccountSerializer
from bluebottle.projects.models import Project
from bluebottle.utils.serializers import MoneySerializer, MoneyTotalSerializer


class PayoutDonationSerializer(serializers.ModelSerializer):

    amount = MoneySerializer(source='payout_amount')
    status = serializers.CharField(source='order.status')
    confirmed = serializers.CharField(source='order.confirmed')
    completed = serializers.CharField(source='order.completed')
    type = serializers.CharField(source='order.order_type')

    payment_method = serializers.SerializerMethodField(source='order.order_payment.payment_method')

    def get_payment_method(self, instance):
        if instance.order.order_type == 'recurring':
            return 'docdata-directdebit'
        if instance.order.order_payment:
            return re.sub('([A-Z]+)', r'-\1', instance.order.order_payment.payment_method).lower()
        return '-unknown-'

    class Meta:
        model = Donation
        fields = ('id', 'type',
                  'amount', 'status',
                  'confirmed', 'completed',
                  'payment_method')


class ProjectPayoutSerializer(serializers.ModelSerializer):
    amount_asked = MoneySerializer(required=False)
    amount_donated = MoneyTotalSerializer(source='totals_donated', read_only=True)

    title = serializers.CharField(required=False)
    account = PayoutAccountSerializer(source='payout_account', read_only=True)

    donations = PayoutDonationSerializer(many=True, read_only=True)
    status = serializers.CharField(source='payout_status')

    target_reached = serializers.SerializerMethodField()

    def get_target_reached(self, obj):
        return obj.status.slug == 'done-complete'

    class Meta:
        model = Project
        fields = ('id',
                  'status',
                  'title',
                  'amount_donated',
                  'amount_asked',
                  'campaign_started',
                  'campaign_ended',
                  'target_reached',
                  'account',
                  'donations'
                  )
