from bluebottle.payments.models import Payment
from django.conf import settings


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
                'email': settings.CONTACT_EMAIL,
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