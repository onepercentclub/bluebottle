from bluebottle.funding.views import PaymentList
from bluebottle.funding_pledge.models import PledgePayment
from bluebottle.funding_pledge.serializers import PledgePaymentSerializer


class PledgePaymentList(PaymentList):
    queryset = PledgePayment.objects.all()
    serializer_class = PledgePaymentSerializer

    def perform_create(self, serializer):
        super(PledgePaymentList, self).perform_create(serializer)
        payment = serializer.instance
        payment.transitions.succeed()
