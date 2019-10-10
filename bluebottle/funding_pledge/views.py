from bluebottle.funding.views import PaymentList
from bluebottle.funding_pledge.models import PledgePayment
from bluebottle.funding_pledge.permissions import PledgePaymentPermission
from bluebottle.funding.permissions import PaymentPermission
from bluebottle.funding_pledge.serializers import PledgePaymentSerializer


class PledgePaymentList(PaymentList):
    queryset = PledgePayment.objects.all()
    serializer_class = PledgePaymentSerializer

    permission_classes = (PaymentPermission, PledgePaymentPermission)

    def perform_create(self, serializer):
        super(PledgePaymentList, self).perform_create(serializer)
        payment = serializer.instance
        payment.transitions.succeed()
