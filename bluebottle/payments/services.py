import re
from django.conf import settings
from bluebottle.utils.utils import import_class
from bluebottle.payments.models import OrderPayment, PaymentAction


def get_payment_methods(country=None, amount=None):
    """
    Get all payment methods from settings.
    """
    # TODO: Add logic to filter methods based on amount and country
    methods = getattr(settings, 'PAYMENT_METHODS', ())
    return methods


class PaymentService(object):

    order_payment = None

    def __init__(self, order_payment=None):
        if not order_payment or not isinstance(order_payment, OrderPayment):
            raise Exception("Need an OrderPayment to in initiate PaymentService")
        self.order_payment = order_payment

    def _get_payment_method(self):
        return self.order_payment.payment_method

    def _get_adapter(self):
        provider_name = re.sub('([a-z]+)([A-Z][a-z]+)', r'\1', self._get_payment_method())
        app_name = 'payments_' + provider_name
        class_name = provider_name.title() + 'PaymentAdapter'
        class_path = 'bluebottle.' + app_name + '.adapters.' + class_name
        return import_class(class_path)

    def _get_or_create_payment(self):
        return self._get_adapter().get_or_create_payment(self.order_payment)

    def start_payment(self):

        # Remove the previous authorization action if there is one
        # FIXME: maybe we want to return this old action rather then generate a new one.
        if self.order_payment.authorization_action:
            self.order_payment.authorization_action.delete()

        payment = self._get_or_create_payment()
        action = self._get_adapter().get_authorization_action(payment)


        self.order_payment.set_authorization_action(action)




