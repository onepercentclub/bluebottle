from rest_framework import serializers

from bluebottle.payouts.models.plain import PlainPayoutAccount


class PlainPayoutAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = PlainPayoutAccount
        fields = ('id',
                  'account_holder_name',
                  'account_number',
                  'account_details',
                  'account_holder_city',
                  'account_holder_country',
                  )
