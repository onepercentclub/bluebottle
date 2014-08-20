from bluebottle.utils.utils import import_class
from django.conf import settings
import re


def get_payment_methods(country=None, amount=None):
    """
    Get all payment methods from settings.
    """
    # TODO: Add logic to filter methods based on amount and country
    methods = getattr(settings, 'PAYMENT_METHODS', ())
    return methods


def get_adapter(name=''):
    """
    Get de PaymentAdapter class based on PaymentMethod name.
    """
    provider_name = re.sub('([a-z]+)([A-Z][a-z]+)', r'\1', name)
    app_name = 'payments_' + provider_name
    class_name = provider_name.title() + 'PaymentAdapter'
    class_path = 'bluebottle.' + app_name + '.adapters.' + class_name
    return import_class(class_path)


class AbstractPaymentAdapter(object):
    """
    This is the abstract base class that should be used by all PaymentAdapters.
    """
    @staticmethod
    def create_payment_object(order_payment, integration_data=None):
        raise NotImplementedError

    @staticmethod
    def get_payment_authorization_action(payment):
        """
        Get an object with payment authorization action.
        Typical response would be
        {'type': 'redirect', 'url' '...', 'method': 'get', 'payload': None}
        """
        raise NotImplementedError

    @staticmethod
    def check_payment_status(payment):
        """
        Fetch the latest payment status from PSP.
        """
        raise NotImplementedError

    @staticmethod
    def cancel_payment(payment):
        """
        Try to cancel the payment at PSP
        """
        raise NotImplementedError


    @staticmethod
    def refund_payment(payment):
        """
        Try to refund the payment at PSP
        """
        raise NotImplementedError

