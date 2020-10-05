from builtins import object
from rest_framework import serializers
from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding_telesom.models import TelesomPayment, TelesomBankAccount


class TelesomPaymentSerializer(PaymentSerializer):
    payment_url = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = TelesomPayment
        fields = PaymentSerializer.Meta.fields + ('payment_url', 'account_number', 'account_name')

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/telesom-payments'

    def create(self, validated_data):
        payment = super(TelesomPaymentSerializer, self).create(validated_data)
        return payment


class TelesomBankAccountSerializer(BaseBankAccountSerializer):

    class Meta(BaseBankAccountSerializer.Meta):
        model = TelesomBankAccount

        fields = BaseBankAccountSerializer.Meta.fields + (
            'account_name',
            'mobile_number',
        )
    included_serializers = {
        'connect_account': 'bluebottle.funding.serializers.PlainPayoutAccountSerializer',
    }

    class JSONAPIMeta(BaseBankAccountSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/telesom-external-accounts'


class PayoutTelesomBankAccountSerializer(serializers.ModelSerializer):
    class Meta(object):
        fields = (
            'id',
            'account_name',
            'mobile_number',
        )

        model = TelesomBankAccount
