from bluebottle.funding.views import PaymentList
from bluebottle.funding_pledge.models import PledgePayment, PledgeBankAccount
from bluebottle.funding_pledge.permissions import PledgePaymentPermission
from bluebottle.funding.permissions import PaymentPermission
from bluebottle.funding_pledge.serializers import PledgePaymentSerializer, PledgeBankAccountSerializer
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import ListCreateAPIView, JsonApiViewMixin, RetrieveUpdateAPIView


class PledgePaymentList(PaymentList):
    queryset = PledgePayment.objects.all()
    serializer_class = PledgePaymentSerializer

    permission_classes = (PaymentPermission, PledgePaymentPermission)

    def perform_create(self, serializer):
        super(PledgePaymentList, self).perform_create(serializer)
        payment = serializer.instance
        payment.transitions.succeed()


class PledgeBankAccountAccountList(JsonApiViewMixin, ListCreateAPIView):
    queryset = PledgeBankAccount.objects.all()
    serializer_class = PledgeBankAccountSerializer
    permission_classes = []

    related_permission_classes = {
        'connect_account': [IsOwner]
    }


class PledgeBankAccountAccountDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = PledgeBankAccount.objects.all()
    serializer_class = PledgeBankAccountSerializer
    permission_classes = []

    related_permission_classes = {
        'connect_account': [IsOwner]
    }
