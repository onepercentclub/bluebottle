from bluebottle.fsm import TransitionManager
from bluebottle.funding.models import Payment
from bluebottle.funding_pledge.transitions import PledgePaymentTransitions


class PledgePayment(Payment):
    transitions = TransitionManager(PledgePaymentTransitions, 'status')

    def save(self, *args, **kwargs):
        if self.status == PledgePaymentTransitions.values.new:
            self.transitions.succeed()

        super(PledgePayment, self).save(*args, **kwargs)
