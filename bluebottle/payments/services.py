import re
import importlib

from bluebottle.clients import properties
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment
from bluebottle.utils.utils import get_class


def check_access_handler(handler, user):
    allowed = False
    try:
        # try to call handler
        parts = handler.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        func = getattr(module, class_name)

        # check if handler 
        allowed = func(user)

    except (ImportError, AttributeError) as e:
        error_message = "Could not import '%s'. %s: %s." % (handler, e.__class__.__name__, e)
        raise Exception(error_message)

    return allowed


def get_payment_methods(country=None, amount=None, user=None):
    """
    Get all payment methods from settings.
    """
    # TODO: Add logic to filter methods based on amount
    all_methods = getattr(properties, 'PAYMENT_METHODS', ())
    if country == 'all':
        return all_methods

    allowed_methods = []

    for method in all_methods:
        allowed = False

        # Check country restrictions
        try:
            countries = method['restricted_countries']
            if country in countries:
                allowed = True
        except KeyError:
            allowed = True

        # Check if the method has an access handler
        try:
            handler = method['method_access_handler']

            if handler:
                allowed = check_access_handler(handler, user)
                method.pop('method_access_handler', None)

        except KeyError:
            pass

        if allowed:
            allowed_methods.append(method)

    return allowed_methods


class PaymentService(object):
    """
    order_payment: OrderPayment
    adapter: a payment adapter e.g. DocdataPaymentAdapter
    payment: a provider payment e.g. DocdataPayment
    """

    def __init__(self, order_payment=None):
        if not order_payment or not isinstance(order_payment, OrderPayment):
            raise Exception(
                "Need an OrderPayment to in initiate PaymentService")

        self.order_payment = order_payment
        self.adapter = self._get_adapter()

    def _get_payment_method(self):
        return self.order_payment.payment_method

    def _get_adapter(self):
        # FIXME: Check if payment_method is set.
        provider_name = re.sub('([a-z]+)([A-Z][a-z]+)', r'\1',
                               self.order_payment.payment_method)
        app_name = 'payments_' + provider_name
        class_name = provider_name.title() + 'PaymentAdapter'
        class_path = 'bluebottle.' + app_name + '.adapters.' + class_name

        try:
            adapter_class = get_class(class_path)
        except ImportError:
            raise PaymentException(
                "Couldn't find an adapter for payment method '{0}'".format(
                    self.order_payment.payment_method))

        adapter = adapter_class(self.order_payment)
        return adapter

    def start_payment(self, **integration_details):
        # Remove the previous authorization action if there is one
        # FIXME: maybe we want to return this old action rather then
        # generate a new one.
        if self.order_payment.authorization_action:
            self.order_payment.authorization_action.delete()

        action = self.adapter.get_authorization_action()
        self.order_payment.set_authorization_action(action)

    def check_payment_status(self, **integration_details):
        self.adapter.check_payment_status()
