from rest_framework import serializers

from bluebottle.payments_lipisha.models import LipishaProject


class BaseProjectAddOnSerializer(serializers.ModelSerializer):

    paybill_number = serializers.CharField()

    class Meta:
        model = LipishaProject
        fields = ('id', 'type', 'account_number', 'paybill_number')
