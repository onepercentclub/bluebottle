import json

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView, View

from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.payments_flutterwave.models import FlutterwavePayment
from bluebottle.utils.utils import get_current_host


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


class FlutterwaveWebhookView(View):
    def post(self, request, **kwargs):
        data = json.loads(request.body)
        payment = FlutterwavePayment.objects.get(transaction_reference=data['txRef'])
        service = PaymentService(payment.order_payment)
        service.check_payment_status()
        return HttpResponse(status=200)
