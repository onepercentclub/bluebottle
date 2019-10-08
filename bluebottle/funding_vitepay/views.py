import logging

from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.funding.exception import PaymentException
from django.http import HttpResponse
from django.views.generic.base import View

from bluebottle.funding.views import PaymentList
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayBankAccount
from bluebottle.funding_vitepay.serializers import VitepayPaymentSerializer, VitepayBankAccountSerializer
from bluebottle.funding_vitepay.utils import update_payment_status
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import JsonApiViewMixin, ListCreateAPIView, RetrieveUpdateAPIView

logger = logging.getLogger(__name__)


class VitepayPaymentList(PaymentList):
    queryset = VitepayPayment.objects.all()
    serializer_class = VitepayPaymentSerializer


class VitepayWebhookView(View):

    def post(self, request, *args, **kwargs):
        success = 'success' in request.POST
        failure = 'failure' in request.POST
        authenticity = request.POST.get('authenticity')
        unique_id = request.POST.get('order_id')
        try:
            payment = VitepayPayment.objects.get(unique_id=unique_id)
        except VitepayPayment.DoesNotExist:
            return HttpResponse('{"status": "0", "message": "Order not found."}')

        try:
            update_payment_status(payment, authenticity, success, failure)
            return HttpResponse('{"status": "1"}')
        except PaymentException as e:
            return HttpResponse('{"status": "0", "message": "%s"}' % e)


class VitepayBankAccountAccountList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = VitepayBankAccount.objects.all()
    serializer_class = VitepayBankAccountSerializer
    permission_classes = []

    related_permission_classes = {
        'connect_account': [IsOwner]
    }


class VitepayBankAccountAccountDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = VitepayBankAccount.objects.all()
    serializer_class = VitepayBankAccountSerializer
    permission_classes = []

    related_permission_classes = {
        'connect_account': [IsOwner]
    }
