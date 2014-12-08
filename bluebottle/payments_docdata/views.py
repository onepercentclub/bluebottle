from django.http import HttpResponse
from django.views.generic import View
from rest_framework import status
from rest_framework import response

from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.models import DocdataPayment, DocdataTransaction
from bluebottle.payments_logger.views import GenericStatusChangedNotificationView
from bluebottle.payments_logger.models import PaymentLogLevels, PaymentLogEntry
from bluebottle.payments_logger.adapters import PaymentLogAdapter
from bluebottle.payments.models import OrderPayment

from .models import DocdataPayment

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
                payment = DocdataPayment.objects.get(merchant_order_id=merchant_order_id)
                order_payment = payment.order_payment
            except DocdataPayment.DoesNotExist:
                raise Exception("Couldn't find Payment for merchant_order_id: {0}".format(merchant_order_id))

        service = PaymentService(order_payment)
        service.check_payment_status()

        return HttpResponse('success')
