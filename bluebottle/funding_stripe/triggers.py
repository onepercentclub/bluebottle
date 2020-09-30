
from bluebottle.fsm.triggers import TransitionTrigger, register
from bluebottle.fsm.effects import RelatedTransitionEffect

from bluebottle.funding.triggers import BasePaymentTriggers, PayoutAccountTriggers
from bluebottle.funding.states import DonationStateMachine


from bluebottle.funding_stripe.models import StripeSourcePayment, StripePayoutAccount
from bluebottle.funding_stripe.states import StripeSourcePaymentStateMachine


@register(StripeSourcePayment)
class StripeSourcePaymentTriggers(BasePaymentTriggers):
    triggers = BasePaymentTriggers.triggers + [
        TransitionTrigger(
            StripeSourcePaymentStateMachine.authorize,
            effects=[
                RelatedTransitionEffect('donation', DonationStateMachine.succeed)
            ]
        ),


        TransitionTrigger(
            StripeSourcePaymentStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('donation', DonationStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            StripeSourcePaymentStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('donation', DonationStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            StripeSourcePaymentStateMachine.dispute,
            effects=[
                RelatedTransitionEffect('donation', DonationStateMachine.refund)
            ]
        ),
    ]


@register(StripePayoutAccount)
class StripePayoutAccountTriggers(PayoutAccountTriggers):
    pass
