from decimal import Decimal, ROUND_HALF_UP
from bluebottle.utils.utils import import_class
from django.conf import settings
from .models import OrderPayment, OrderPaymentStatuses, PaymentLogLevels
from .signals import payment_status_changed
from django.conf import settings
import re
from django.db.models import get_model

def get_payment_methods(country=None, amount=None):
    methods = getattr(settings, 'PAYMENT_METHODS', ())
    return methods


def get_adapter(name=''):
    provider_name = re.sub('([a-z]+)([A-Z][a-z]+)', r'\1', name)
    app_name = 'payments_' + provider_name
    class_name = provider_name.title() + 'PaymentAdapter'
    class_path = 'bluebottle.' + app_name + '.adapters.' + class_name
    return import_class(class_path)


class AbstractPaymentAdapter(object):
    """
    This is the abstract base class that should be used by all Payment Adapters.
    """

    def get_payment_methods(self):
        raise NotImplementedError

    @staticmethod
    def create_payment_object(order_payment, integration_data=None):
        raise NotImplementedError

    @staticmethod
    def get_payment_authorization_action(payment):
        raise NotImplementedError

    @staticmethod
    def check_payment_status(payment):
        raise NotImplementedError

    @staticmethod
    def cancel_payment(payment):
        raise NotImplementedError

