from django.http import HttpResponse
from django.views.generic import View

from bluebottle.payments.exception import PaymentException
from bluebottle.payments.services import PaymentService
from bluebottle.payments_vitepay.models import VitepayPayment


class PaymentStatusListener(View):
    """
    Listens to Vitepay updates.
    """

    def post(self, request, *args, **kwargs):
        success = 'success' in request.POST
        failure = 'failure' in request.POST
        authenticity = request.POST.get('authenticity')
        order_id = request.POST.get('order_id')

        try:
            payment = VitepayPayment.objects.get(order_id=order_id)
            order_payment = payment.order_payment
        except VitepayPayment.DoesNotExist:
            return HttpResponse('{"status": "0", "message": "Order not found."}')

        service = PaymentService(order_payment)

        # We pass the post params to the adapter to do the status update

        try:
            service.adapter.status_update(authenticity, success, failure)
            return HttpResponse('{"status": "1"}')
        except PaymentException as e:
            return HttpResponse('{"status": "0", "message": "%s"}' % e)
