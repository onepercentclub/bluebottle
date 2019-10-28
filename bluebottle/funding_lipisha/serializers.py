from rest_framework import serializers

from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaBankAccount


class LipishaPaymentSerializer(PaymentSerializer):
    transaction = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = LipishaPayment
        fields = PaymentSerializer.Meta.fields + (
            'mobile_number',
            'transaction')

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/lipisha-payments'


class LipishaBankAccountSerializer(BaseBankAccountSerializer):

    class Meta(BaseBankAccountSerializer.Meta):
        model = LipishaBankAccount

        fields = BaseBankAccountSerializer.Meta.fields + (
            'account_name',
            'account_number',
            'bank_name',
            'bank_code',
            'branch_name',
            'branch_code',
            'address',
            'swift',
        )

    included_serializers = {
        'connect_account': 'bluebottle.funding.serializers.PlainPayoutAccountSerializer',
    }

    class JSONAPIMeta(BaseBankAccountSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/lipisha-external-accounts'
