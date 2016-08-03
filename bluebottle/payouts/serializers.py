from rest_framework import serializers

from bluebottle.utils.serializers import MoneySerializer
from .models import ProjectPayout


class PayoutSerializer(serializers.ModelSerializer):

    amount = MoneySerializer(source='amount_payable')

    class Meta:
        model = ProjectPayout
        fields = ('id', 'amount', 'project',
                  'receiver_account_number',
                  'receiver_account_iban',
                  'receiver_account_bic',
                  'receiver_account_name',
                  'receiver_account_city',
                  'receiver_account_country'
                  )
