from rest_framework import serializers

from bluebottle.utils.serializers import MoneySerializer
from .models import ProjectPayout


class PayoutSerializer(serializers.ModelSerializer):

    amount = MoneySerializer(source='amount_payable')

    receiver_account_name = serializers.CharField(source='account_holder_name')
    receiver_account_number = serializers.CharField(source='account_number')
    receiver_account_bic = serializers.CharField(source='account_bic')
    receiver_account_city = serializers.CharField(source='account_holder_city')
    receiver_account_country = serializers.CharField(source='account_holder_country.name')

    class Meta:
        model = ProjectPayout
        fields = ('id', 'amount', 'project',
                  'receiver_account_name',
                  'receiver_account_number',
                  'receiver_account_bic',
                  'receiver_account_city',
                  'receiver_account_country'
                  )
