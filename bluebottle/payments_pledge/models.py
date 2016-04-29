from bluebottle.payments.models import Payment


class PledgeStandardPayment(Payment):
    """ Pledge payment class."""

    def get_method_name(self):
        return 'Pledge'