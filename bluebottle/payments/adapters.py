from bluebottle.utils.utils import import_class
from django.conf import settings
import re


class AbstractPaymentAdapter(object):
    """
    This is the abstract base class that should be used by all PaymentAdapters.
    """

    @classmethod
    def create_payment(cls, order_payment):
        """
        Create a Payment specific to the chosen provider/payment_method
        """
        raise NotImplementedError

    @classmethod
    def get_payment_authorization_action(cls, order_payment):
        """
        Get an object with payment authorization action.
        Typical response would be
        {'type': 'redirect', 'url' '...', 'method': 'get', 'payload': None}
        """
        raise NotImplementedError

    @classmethod
    def check_payment_status(cls, order_payment):
        """
        Fetch the latest payment status from PSP.
        """
        raise NotImplementedError

    @classmethod
    def cancel_payment(cls, order_payment):
        """
        Try to cancel the payment at PSP
        """
        raise NotImplementedError


    @classmethod
    def refund_payment(cls, order_payment):
        """
        Try to refund the payment at PSP
        """
        raise NotImplementedError

