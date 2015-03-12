import logging
import re

from bluebottle.payments_logger.models import PaymentLogEntry, PaymentLogLevels
from rest_framework import generics, response, status

logger = logging.getLogger(__name__)


# TODO: limit status change notifications to docdata IPs
class GenericStatusChangedNotificationView(generics.GenericAPIView):

    def get(self, request, *args, **kwargs):

        # is it 'order' what I am looking for?
        if 'order' in request.QUERY_PARAMS:
            order_id = request.QUERY_PARAMS['order']
            if re.match('^[0-9]+-[0-9]+$', order_id):

                # Try to find the payment for this order.
                payment = self._find_payment(order_id)

                # Update the status for the payment.
                self._update_status(payment, order_id)

                # Return 200 as required by DocData when the status changed notification was consumed.
                return response.Response(status=status.HTTP_200_OK)
            else:
                logger.error('Could not match order {0} to update payment status.'.format(order_id))
        return response.Response(status=status.HTTP_403_FORBIDDEN)

    def _update_status(self, payment, order_id):
        status_log = PaymentLogEntry(payment=payment, level=PaymentLogLevels.info)
        status_log.message = 'Received status changed notification for merchant_order_reference {0}.'.format(order_id)
        status_log.save()

        # The following we had in cowry_docdata, don't know if we need it here.
        # if so we have to implement a update_payment_status method in the adapter(?)
        # payments.update_payment_status(payment, status_changed_notification=True)

    def _find_payment(self, order_id):
        #TODO: To be implemented in the sub classes
        # for example like this
        # try:
        #     payment = PaymentClass.objects.get(merchant_order_reference=order_id)
        # except PaymentClass.DoesNotExist:
        #     logger.error('Could not find order {0} to update payment status.'.format(order_id))
        #     return response.Response(status=status.HTTP_403_FORBIDDEN)
        # return payment
        pass
