from django.shortcuts import get_object_or_404
from django.views.generic.base import RedirectView

from bluebottle.payments.models import OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.utils.utils import get_current_host


class PaymentResponseView(RedirectView):

    permanent = False
    query_string = True
    pattern_name = 'telesom-payment-response'

    def get_redirect_url(self, *args, **kwargs):
        order_payment = get_object_or_404(OrderPayment, id=kwargs['order_payment_id'])
        service = PaymentService(order_payment)
        service.check_payment_status()

        return "{0}/orders/{1}/success".format(get_current_host(), order_payment.order.id)
