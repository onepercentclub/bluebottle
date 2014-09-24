from django.http import HttpResponse
from django.views.generic import View
from rest_framework import status
from rest_framework import response
from bluebottle.payments.services import PaymentService
from bluebottle.payments_docdata.models import DocdataPayment, DocdataTransaction
from bluebottle.payments_logger.views import GenericStatusChangedNotificationView
from bluebottle.payments_logger.models import PaymentLogLevels, PaymentLogEntry
from bluebottle.payments_logger.adapters import PaymentLogAdapter
from .models import DocdataPayment

import logging
logger = logging.getLogger(__name__)


class DocdataStatusChangedNotificationView( ):

    def _find_payment(self, order_id):
        try:
            payment = DocdataPayment.objects.get(merchant_order_id=order_id)
        except DocdataPayment.DoesNotExist:
            logger.error('Could not find order {0} to update payment status.'.format(order_id))
            return response.Response(status=status.HTTP_403_FORBIDDEN)
        return payment


class PaymentStatusUpdateView(View):

    def get(self, request, **kwargs):
        payment_cluster_id = kwargs['payment_cluster_id']
        try:
            payment = DocdataPayment.objects.get(payment_cluster_id=payment_cluster_id)
        except DocdataPayment.DoesNotExist:
            raise Exception("Couldn't find DocdataPayment with payment cluster id: {0}".format(payment_cluster_id))

        service = PaymentService(payment.order_payment)
        service.check_payment_status()

        # Get the docdata transactions
        try:
            transaction = DocdataTransaction.objects.get(payment=payment)
        except DocdataPayment.DoesNotExist:
             raise Exception("Couldn't find DocdataTransaction for payment: {0}".format(payment))

        # Map Docdata payment method naming to our naming convention
        if transaction:
            original_method = payment.order_payment.payment_method
            new_method = service.adapter.PAYMENT_METHODS.get(transaction.payment_method, 'unknown')
            if new_method != original_method:
                payment.order_payment.payment_method = new_method           
                payment.order_payment.save()

                payment_logger = PaymentLogAdapter()
                payment_logger.log(payment, 'info', 'Payment method changed for payment with id {0} and order payment with id {1}.'.format(payment.id, payment.order_payment.id))

        return HttpResponse('success')
