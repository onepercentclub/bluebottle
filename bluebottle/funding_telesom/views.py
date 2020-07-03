import logging

from django.http import HttpResponse
from django.views.generic.base import View
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.funding.exception import PaymentException
from bluebottle.funding.views import PaymentList
from bluebottle.funding_telesom.models import TelesomPayment, TelesomBankAccount
from bluebottle.funding_telesom.serializers import TelesomPaymentSerializer, TelesomBankAccountSerializer
from bluebottle.funding_telesom.utils import update_payment_status
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import JsonApiViewMixin, ListCreateAPIView, RetrieveUpdateAPIView

logger = logging.getLogger(__name__)


class TelesomPaymentList(PaymentList):
    queryset = TelesomPayment.objects.all()
    serializer_class = TelesomPaymentSerializer


class TelesomWebhookView(View):

    def post(self, request, *args, **kwargs):
        success = 'success' in request.POST
        failure = 'failure' in request.POST
        authenticity = request.POST.get('authenticity')
        unique_id = request.POST.get('order_id')
        try:
            payment = TelesomPayment.objects.get(unique_id=unique_id)
        except TelesomPayment.DoesNotExist:
            return HttpResponse('{"status": "0", "message": "Order not found."}')

        try:
            update_payment_status(payment, authenticity, success, failure)
            return HttpResponse('{"status": "1"}')
        except PaymentException as e:
            return HttpResponse('{"status": "0", "message": "%s"}' % e)


class TelesomBankAccountAccountList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = TelesomBankAccount.objects.all()
    serializer_class = TelesomBankAccountSerializer
    permission_classes = []

    related_permission_classes = {
        'connect_account': [IsOwner]
    }


class TelesomBankAccountAccountDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = TelesomBankAccount.objects.all()
    serializer_class = TelesomBankAccountSerializer
    permission_classes = []

    related_permission_classes = {
        'connect_account': [IsOwner]
    }
