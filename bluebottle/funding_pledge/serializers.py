from bluebottle.funding.base_serializers import PaymentSerializer, BaseBankAccountSerializer
from bluebottle.funding_pledge.models import PledgePayment, PledgeBankAccount


class PledgePaymentSerializer(PaymentSerializer):
    class Meta(PaymentSerializer.Meta):
        model = PledgePayment

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/pledge-payments'


class PledgeBankAccountSerializer(BaseBankAccountSerializer):

    class Meta(BaseBankAccountSerializer.Meta):
        model = PledgeBankAccount

        fields = BaseBankAccountSerializer.Meta.fields + (
            'account_holder_name',
            'account_holder_address',
            'account_holder_postal_code',
            'account_holder_city',
            'account_holder_country',
            'account_number',
            'account_details',
            'account_bank_country',
        )

    included_serializers = {
        'connect_account': 'bluebottle.funding.serializers.PlainPayoutAccountSerializer',
    }

    class JSONAPIMeta(BaseBankAccountSerializer.JSONAPIMeta):
        resource_name = 'payout-accounts/pledge-external-accounts'
