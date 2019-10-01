from bluebottle.funding.base_serializers import PaymentSerializer
from bluebottle.funding_pledge.models import PledgePayment


class PledgePaymentSerializer(PaymentSerializer):
    class Meta(PaymentSerializer.Meta):
        model = PledgePayment

    class JSONAPIMeta(PaymentSerializer.JSONAPIMeta):
        resource_name = 'payments/pledge-payments'
