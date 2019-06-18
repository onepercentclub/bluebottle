from django.views.generic import View
from django.http import HttpResponse

from bluebottle.funding.exception import PaymentException
from bluebottle.funding.views import PaymentList
from bluebottle.funding_vitepay.adapters import VitepayPaymentAdapter
from bluebottle.funding_vitepay.models import VitepayPayment
from bluebottle.funding_vitepay.serializers import VitepayPaymentSerializer


class StripePaymentList(PaymentList):
    queryset = VitepayPayment.objects.all()
    serializer_class = VitepayPaymentSerializer


class WebHookView(View):

    def post(self, request, *args, **kwargs):
        success = 'success' in request.POST
        failure = 'failure' in request.POST
        authenticity = request.POST.get('authenticity')
        order_id = request.POST.get('order_id')

        try:
            payment = self.get_payment(order_id=order_id)
        except VitepayPayment.DoesNotExist:
            return HttpResponse('{"status": "0", "message": "Order not found."}')

        try:
            adapter = VitepayPaymentAdapter(payment)
            adapter.status_update(authenticity, success, failure)

            return HttpResponse('{"status": "1"}')
        except PaymentException as e:
            return HttpResponse('{"status": "0", "message": "%s"}' % e)

    def get_payment(self, order_id):
        try:
            return VitepayPayment.objects.get(order_id=order_id)
        except VitepayPayment.DoesNotExist:
            return HttpResponse('{"status": "0", "message": "Payment not Found"}')
