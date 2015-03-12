from bluebottle.clients import properties
from bluebottle.payments.models import Payment
from bluebottle.payments_logger.adapters import PaymentLogAdapter
from django.conf import settings


class BasePaymentAdapter(object):
    """
    This is the abstract base class that should be used by all PaymentAdapters.
    """

    MODEL_CLASSES = [Payment]

    def __init__(self, order_payment):

        self.payment_logger = PaymentLogAdapter()
        self.order_payment = order_payment
        self.payment = None

        if len(self.MODEL_CLASSES) == 1 and self.MODEL_CLASSES[0].__class__ == Payment:
            raise Exception("Please override MODEL_CLASSES with extended payment model(s).")

        for i in range(0, len(self.MODEL_CLASSES)):
            cls = self.MODEL_CLASSES[i]
            try:
                self.payment = cls.objects.get(order_payment=self.order_payment)
                break
            except cls.MultipleObjectsReturned:
                raise Exception("Multiple payments for OrderPayment {0}".format(self.order_payment))
            except cls.DoesNotExist:
                # Pass here to allow for other classes in MODEL_CLASSES
                pass

        # Finally if no payment found then create a new one
        if not self.payment:
            self.payment = self.create_payment()

    def get_user_data(self):
        user = self.order_payment.order.user
        if user:
            user_data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            }
        else:
            user_data = {
                'id': None,
                'first_name': 'Nomen',
                'last_name': 'Nescio',
                'email': properties.CONTACT_EMAIL,
            }
        return user_data

    def create_payment(self):
        """
        Create a Payment specific to the chosen provider/payment_method
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

    def _get_mapped_status(self, status):
        """
        Map the status of the PSP to our own status pipeline
        """
        raise NotImplementedError

    def get_authorization_action(self):
        """
        Create the AuthorizationAction for the PSP
        """
        raise NotImplementedError
