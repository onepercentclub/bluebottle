from rest_framework import serializers

from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwaveBankAccount


class FlutterwavePaymentSerializer(PaymentSerializer):
    tx_ref = serializers.CharField(required=True)

    class Meta(PaymentSerializer.Meta):
        model = FlutterwavePayment
        fields = PaymentSerializer.Meta.fields + ('tx_ref', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/flutterwave-payments'


class FlutterwaveBankAccountSerializer(BaseBankAccountSerializer):

    class Meta(BaseBankAccountSerializer.Meta):
        model = FlutterwaveBankAccount

        fields = BaseBankAccountSerializer.Meta.fields + (
            'account_holder_name',
            'bank_code',
            'account_number'
        )

    included_serializers = {
        'connect_account': 'bluebottle.funding.serializers.PlainPayoutAccountSerializer',
    }

    class JSONAPIMeta(BaseBankAccountSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/flutterwave-external-accounts'


class PayoutFlutterwaveBankAccountSerializer(serializers.ModelSerializer):

    class Meta(BaseBankAccountSerializer.Meta):
        model = FlutterwaveBankAccount

        fields = (
            'id',
            'account_holder_name',
            'bank_code',
            'bank_country_code',
            'account_number',
            'account',
        )
