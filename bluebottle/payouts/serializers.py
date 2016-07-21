from rest_framework import serializers

from bluebottle.utils.serializers import MoneySerializer
from .models import ProjectPayout


class PayoutSerializer(serializers.ModelSerializer):

    amount_payable = MoneySerializer()

    class Meta:
        model = ProjectPayout
        fields = ('id', 'amount_payable', 'project')
