import re
import importlib

from bluebottle.clients import properties
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import OrderPayment
from bluebottle.projects.models import Project
from bluebottle.utils.utils import get_class, GetClassError


def check_access_handler(handler, user):
    if handler is None:
        return True

    try:
        # try to call handler
        parts = handler.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        func = getattr(module, class_name)

        # check if handler
        return func(user)

    except (ImportError, AttributeError) as e:
        error_message = "Could not import '%s'. %s: %s." % (handler, e.__class__.__name__, e)
        raise Exception(error_message)


def get_payment_methods(country=None, amount=None, user=None, currency=None, project_id=None):
    """
    Get payment methods from settings
    """
    # TODO: Add logic to filter methods based on amount
    methods = getattr(properties, 'PAYMENT_METHODS', ())

    # Filter on restricted countries if it is set
    if country:
        methods = [
            method for method in methods
            if country in method.get('restricted_countries', [country])
        ]

    # Filter out methods that do not support the currency
    if currency:
        methods = [
            method for method in methods
            if currency in method.get('currencies', {}).keys()
        ]

    if project_id:
        try:
            project = Project.objects.get(pk=project_id)
            methods = [
                method for method in methods
                if method.get('provider') in project.payout_account.providers
            ]
        except Project.DoesNotExist:
            pass

    # Filter out methods that are resitrcted using an access handler function
    return [
        method for method in methods
        if check_access_handler(
            method.pop('method_access_handler', None), user)
    ]


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
        method_name = re.sub('([a-z]+)([A-Z][a-z]+)', r'\2',
                             self.order_payment.payment_method)
        app_name = 'payments_' + provider_name

        # First try to load the specific profile adapter
        class_name = provider_name.title() + method_name + 'PaymentAdapter'
        class_path = 'bluebottle.' + app_name + '.adapters.' + class_name
        try:
            adapter_class = get_class(class_path)
        except GetClassError:
            # Now try to load the generic provider adapter
            class_name = provider_name.title() + 'PaymentAdapter'
            class_path = 'bluebottle.' + app_name + '.adapters.' + class_name
            try:
                adapter_class = get_class(class_path)
            except GetClassError:
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

    def refund_payment(self):
        self.adapter.refund_payment()
