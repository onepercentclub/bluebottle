from bluebottle.fsm import transition
from bluebottle.funding.transitions import PaymentTransitions


class PledgePaymentTransitions(PaymentTransitions):
    @transition(
        source=[PaymentTransitions.values.success],
        target=PaymentTransitions.values.refund_requested
    )
    def request_refund(self):
        self.refund()
