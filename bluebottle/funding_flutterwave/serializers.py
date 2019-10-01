from rest_framework import serializers

from bluebottle.funding.base_serializers import PaymentSerializer
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwaveBankAccount


class FlutterwavePaymentSerializer(PaymentSerializer):
    tx_ref = serializers.CharField(required=True)

    class Meta(PaymentSerializer.Meta):
        model = FlutterwavePayment
        fields = PaymentSerializer.Meta.fields + ('tx_ref', )

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/flutterwave-payments'


class FlutterwaveBankAccountSerializer(serializers.ModelSerializer):

    class Meta:
        model = FlutterwaveBankAccount

        fields = (
            'id', 'account_holder_name', 'bank_code', 'account_number',

        )

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/flutterwave-external-accounts'
