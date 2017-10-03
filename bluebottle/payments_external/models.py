from bluebottle.payments.models import Payment


class ExternalPayment(Payment):

    def get_method_name(self):
        """ Return the payment method name."""
        return 'external'

    def get_fee(self):
        """
        We don't calculate fee over external payments
        """
        return 0
