from bluebottle.payments.models import Payment
from bluebottle.utils.utils import import_class
from django.conf import settings
import re


class BasePaymentAdapter(object):
    """
    This is the abstract base class that should be used by all PaymentAdapters.
    """

    MODEL_CLASS = Payment

    def __init__(self, order_payment):
        self.order_payment = order_payment
        if self.MODEL_CLASS.__class__ == Payment:
            raise Exception("Please override MODEL_CLASS with extended payment model.")

        try:
            self.payment = self.MODEL_CLASS.objects.get(order_payment=self.order_payment)
        except self.MODEL_CLASS.DoesNotExist:
            self.payment = self.create_payment()
        except self.MODEL_CLASS.MultipleObjectsReturned:
            raise Exception("Multiple payments for OrderPayment {0}".format(self.order_payment))

    def create_payment(self):
        """
        Create a Payment specific to the chosen provider/payment_method
        """
        raise NotImplementedError

    def get_payment_authorization_action(self):
        """
        Get an object with payment authorization action.
        Typical response would be
        {'type': 'redirect', 'url' '...', 'method': 'get', 'payload': None}
        """
        raise NotImplementedError

    def check_payment_status(self):
        """
        Fetch the latest payment status from PSP.
        """
        raise NotImplementedError

    def cancel_payment(self):
        """
        Try to cancel the payment at PSP
        """
        raise NotImplementedError

    def refund_payment(self):
        """
        Try to refund the payment at PSP
        """
        raise NotImplementedError

