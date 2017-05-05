from bluebottle.payments.models import Payment


# TODO: do we need a pledge payment model?
class PledgeStandardPayment(Payment):
    """ Pledge payment class."""

    @property
    def transaction_reference(self):
        return self.id

    def get_method_name(self):
        return 'Pledge'

import signals  # noqa
