import re

from bluebottle.clients import properties
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment
from bluebottle.utils.utils import import_class


def get_payment_methods(country=None, amount=None):
    """
    Get all payment methods from settings.
    """
    # TODO: Add logic to filter methods based on amount
    all_methods = getattr(properties, 'PAYMENT_METHODS', ())
    if country == 'all':
        return all_methods

    allowed_methods = []

    for method in all_methods:
        try:
            countries = method['restricted_countries']
            if country in countries:
                allowed_methods.append(method)
        except KeyError:
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
            adapter_class = import_class(class_path)
        except ImportError:
            raise PaymentException(
                "Couldn't find an adapter for payment method '{0}'".format(
                    self.order_payment.payment_method))

        adapter = adapter_class(self.order_payment)
        return adapter

    def start_payment(self, **integration_details):
        # Remove the previous authorization action if there is one
        # FIXME: maybe we want to return this old action rather then generate a new one.
        if self.order_payment.authorization_action:
            self.order_payment.authorization_action.delete()

        action = self.adapter.get_authorization_action()
        self.order_payment.set_authorization_action(action)

    def check_payment_status(self, **integration_details):
        self.adapter.check_payment_status()
