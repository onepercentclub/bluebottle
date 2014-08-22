from rest_framework import response
from rest_framework import status
from bluebottle.payments_logger.views import GenericStatusChangedNotificationView
from .models import DocdataPayment

import logging
logger = logging.getLogger(__name__)


class DocdataStatusChangedNotificationView(GenericStatusChangedNotificationView):

    def _find_payment(self, order_id):
        try:
            payment = DocdataPayment.objects.get(merchant_order_id=order_id)
        except DocdataPayment.DoesNotExist:
            logger.error('Could not find order {0} to update payment status.'.format(order_id))
            return response.Response(status=status.HTTP_403_FORBIDDEN)
        return payment
