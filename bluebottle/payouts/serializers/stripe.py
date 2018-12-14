from rest_framework import serializers

from bluebottle.payouts.models.stripe import StripePayoutAccount


class StripePayoutAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = StripePayoutAccount
        fields = ('id',
                  'account_token',
                  'verified',
                  )
