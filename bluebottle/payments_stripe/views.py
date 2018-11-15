from django.http import HttpResponse
from django.views.generic import View

from bluebottle.payments.services import PaymentService
from bluebottle.payments.models import OrderPayment

from .models import StripePayment

import logging

logger = logging.getLogger(__name__)


class PaymentStatusUpdateView(View):
    def get(self, request, **kwargs):
        merchant_order_id = kwargs['merchant_order_id']
        try:
            # Try to load new style OrderPayment
            order_payment_id = merchant_order_id.split('-')[0]
            order_payment = OrderPayment.objects.get(pk=order_payment_id)
        except OrderPayment.DoesNotExist:
            # Try to load old style DocdataPayment.
            try:
                payment = StripePayment.objects.get(
                    merchant_order_id=merchant_order_id)
                order_payment = payment.order_payment
            except StripePayment.DoesNotExist:
                raise Exception(
                    "Couldn't find Payment for merchant_order_id: {0}".format(
                        merchant_order_id))

        service = PaymentService(order_payment)
        service.check_payment_status()

        return HttpResponse('success')
