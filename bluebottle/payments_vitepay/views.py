from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.views.generic.base import RedirectView

from bluebottle.payments.models import OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.utils.utils import get_current_host


class PaymentResponseView(RedirectView):

    permanent = False
    query_string = True
    pattern_name = 'vitepay-payment-response'

    def get_redirect_url(self, *args, **kwargs):
        order_payment = get_object_or_404(OrderPayment, id=kwargs['order_payment_id'])
        service = PaymentService(order_payment)
        service.check_payment_status()
        return "{0}/orders/{1}/success".format(get_current_host(), order_payment.order.id)


class PaymentStatusListener(View):
    """
    This view simulates our listener that handles incoming messages from an external PSP to update the status of
    a payment. It's an "underwater" view and the user does not directly engage with this view or url, only the
    external server by making a POST request to it.
    """

    def post(self, request, *args, **kwargs):
        status = request.POST.get('status', None)
        order_payment_id = request.POST.get('order_payment_id')

        try:
            order_payment = OrderPayment.objects.get(id=order_payment_id)
        except OrderPayment.DoesNotExist:
            raise Http404

        service = PaymentService(order_payment)

        # We pass the MockPayment status and get back the status name of our OrderStatus definition
        service.adapter.set_order_payment_new_status(status)

        return HttpResponse('success')
