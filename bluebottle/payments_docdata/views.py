from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.models import DocdataPayment
from django.http import HttpResponse
from django.views.generic import View


class PaymentStatusUpdateView(View):

    def get(self, request, **kwargs):
        payment_cluster_id = kwargs['payment_cluster_id']
        try:
            payment = DocdataPayment.objects.get(payment_cluster_id=payment_cluster_id)
        except DocdataPayment.DoesNotExist:
            raise Exception("Couldn't find DocdataPayment with payment cluster id: {0}".format(payment_cluster_id))

        service = PaymentService(payment.order_payment)
        service.check_payment_status()

        return HttpResponse('success')
