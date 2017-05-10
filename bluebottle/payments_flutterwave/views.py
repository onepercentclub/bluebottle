import json

from django.http.response import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView, View

from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.utils.utils import get_current_host

from .models import FlutterwaveMpesaPayment


class PaymentResponseView(RedirectView):

    permanent = False
    query_string = True
    pattern_name = 'flutterwave-payment-response'

    def get_redirect_url(self, *args, **kwargs):
        order_payment = get_object_or_404(OrderPayment, id=kwargs['order_payment_id'])
        service = PaymentService(order_payment)
        try:
            service.check_payment_status()
            return "{0}/orders/{1}/success".format(get_current_host(), order_payment.order.id)
        except PaymentException:
            return "{0}/orders/{1}/failed".format(get_current_host(), order_payment.order.id)


class MpesaPaymentUpdateView(View):

    def post(self, request, *args, **kwargs):
        payload = json.loads(request.body)
        try:
            payment = FlutterwaveMpesaPayment.objects.get(account_number=payload['billrefnumber'])
        except FlutterwaveMpesaPayment.DoesNotExist:
            raise Http404('No payment found with this billrefnumber.')
        service = PaymentService(payment.order_payment)
        service.adapter.update_mpesa(**payload)
        return HttpResponse(status=200, content={'success': 1})
