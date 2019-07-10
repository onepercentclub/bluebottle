from bluebottle.fsm import transition
from bluebottle.funding.transitions import PaymentTransitions
from bluebottle.funding_stripe.utils import init_stripe


class StripePaymentTransitions(PaymentTransitions):
    @transition(
        source=[PaymentTransitions.values.success],
        target=PaymentTransitions.values.refund_requested
    )
    def request_refund(self):
        stripe = init_stripe()
        intent = stripe.PaymentIntent.retrieve(self.instance.intent_id)

        intent.charges[0].refund(
            reverse_transfer=True,
        )
