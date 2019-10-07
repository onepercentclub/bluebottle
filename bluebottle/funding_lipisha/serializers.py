from rest_framework import serializers

from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaBankAccount


class LipishaPaymentSerializer(PaymentSerializer):
    transaction = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = LipishaPayment
        fields = PaymentSerializer.Meta.fields + ('mobile_number', 'transaction')

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/lipisha-payments'


class LipishaBankAccountSerializer(BaseBankAccountSerializer):

    class Meta:
        model = LipishaBankAccount

        fields = (
            'id', 'account_holder_name', 'bank_code', 'account_number',

        )

    class JSONAPIMeta(object):
        resource_name = 'payout-accounts/lipisha-external-accounts'
