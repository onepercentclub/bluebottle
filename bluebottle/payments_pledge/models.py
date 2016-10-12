from bluebottle.payments.models import Payment


# TODO: do we need a pledge payment model?
class PledgeStandardPayment(Payment):
    """ Pledge payment class."""

    def get_method_name(self):
        return 'Pledge'

import signals  # noqa
