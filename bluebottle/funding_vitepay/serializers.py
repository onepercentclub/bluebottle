from rest_framework import serializers
from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayBankAccount
from bluebottle.funding_vitepay.utils import get_payment_url


class VitepayPaymentSerializer(PaymentSerializer):
    payment_url = serializers.CharField(read_only=True)

    class Meta(PaymentSerializer.Meta):
        model = VitepayPayment
        fields = PaymentSerializer.Meta.fields + ('payment_url', 'mobile_number')

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/vitepay-payments'

    def create(self, validated_data):
        payment = super(VitepayPaymentSerializer, self).create(validated_data)
        payment.payment_url = get_payment_url(payment)
        return payment


class VitepayBankAccountSerializer(BaseBankAccountSerializer):

    class Meta(BaseBankAccountSerializer.Meta):
        model = VitepayBankAccount

        fields = BaseBankAccountSerializer.Meta.fields + (
            'account_name',
            'mobile_number',
        )
    included_serializers = {
        'connect_account': 'bluebottle.funding.serializers.PlainPayoutAccountSerializer',
    }

    class JSONAPIMeta(BaseBankAccountSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/vitepay-external-accounts'
