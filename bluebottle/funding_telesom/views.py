import logging

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest
from django.views.generic.base import View
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.funding.exception import PaymentException
from bluebottle.funding.views import PaymentList
from bluebottle.funding_telesom.models import TelesomPayment, TelesomBankAccount
from bluebottle.funding_telesom.serializers import TelesomPaymentSerializer, TelesomBankAccountSerializer
from bluebottle.funding_telesom.utils import initiate_payment
from bluebottle.utils.permissions import IsOwner
from bluebottle.utils.views import JsonApiViewMixin, ListCreateAPIView, RetrieveUpdateAPIView

logger = logging.getLogger(__name__)


class TelesomPaymentList(PaymentList):
    queryset = TelesomPayment.objects.all()
    serializer_class = TelesomPaymentSerializer

    def perform_create(self, serializer):
        super(TelesomPaymentList, self).perform_create(serializer)
        initiate_payment(serializer.save())


class TelesomWebhookView(View):

    def post(self, request, *args, **kwargs):
        unique_id = request.POST.get('order_id')
        try:
            payment = TelesomPayment.objects.get(unique_id=unique_id)
        except TelesomPayment.DoesNotExist:
            return HttpResponseNotFound('Telesom payment not found')

        try:
            initiate_payment(payment)
            return HttpResponse('SUCCESS')
        except PaymentException as e:
            return HttpResponseBadRequest('Error updating Telesom payment: {}'.format(e))


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
