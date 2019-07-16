import logging

from bluebottle.funding.exception import PaymentException
from django.http import HttpResponse
from django.views.generic.base import View

from bluebottle.funding.views import PaymentList
from bluebottle.funding_vitepay.models import VitepayPayment
from bluebottle.funding_vitepay.serializers import VitepayPaymentSerializer
from bluebottle.funding_vitepay.utils import update_payment_status

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
            payment = self.get_payment(unique_id=unique_id)
        except VitepayPayment.DoesNotExist:
            return HttpResponse('{"status": "0", "message": "Order not found."}')

        try:
            update_payment_status(payment, authenticity, success, failure)
            return HttpResponse('{"status": "1"}')
        except PaymentException as e:
            return HttpResponse('{"status": "0", "message": "%s"}' % e)

    def get_payment(self, unique_id):
        try:
            return VitepayPayment.objects.get(unique_id=unique_id)
        except VitepayPayment.DoesNotExist:
            return HttpResponse('{"status": "0", "message": "Payment not Found"}')
