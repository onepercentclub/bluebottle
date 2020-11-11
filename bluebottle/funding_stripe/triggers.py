from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger, register
from bluebottle.funding.states import DonationStateMachine, PayoutAccountStateMachine
from bluebottle.funding.triggers import BasePaymentTriggers, PayoutAccountTriggers, BankAccountTriggers
from bluebottle.funding_stripe.models import StripeSourcePayment, StripePayoutAccount, ExternalAccount
from bluebottle.funding_stripe.states import StripeSourcePaymentStateMachine, StripePayoutAccountStateMachine


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


def account_verified(effect):
    """connected payout account is verified"""
    return effect.instance.connect_account.status == PayoutAccountStateMachine.verified.value


@register(ExternalAccount)
class StripeBankAccountTriggers(BankAccountTriggers):

    triggers = PayoutAccountTriggers.triggers + [
        TransitionTrigger(
            StripePayoutAccountStateMachine.initiate,
            effects=[
                TransitionEffect(
                    'verify',
                    conditions=[account_verified]
                )
            ]
        )
    ]
