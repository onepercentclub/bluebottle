from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger, register, TriggerManager
from bluebottle.funding.effects import SubmitConnectedActivitiesEffect
from bluebottle.funding.messages import PayoutAccountVerified, PayoutAccountRejected
from bluebottle.funding.states import DonationStateMachine, PayoutAccountStateMachine
from bluebottle.funding.triggers import BasePaymentTriggers
from bluebottle.funding_stripe.models import StripeSourcePayment, StripePayoutAccount, ExternalAccount
from bluebottle.funding_stripe.states import StripeSourcePaymentStateMachine, StripeBankAccountStateMachine
from bluebottle.notifications.effects import NotificationEffect


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
class StripePayoutAccountTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            PayoutAccountStateMachine.verify,
            effects=[
                NotificationEffect(PayoutAccountVerified),
                RelatedTransitionEffect(
                    'external_accounts',
                    StripeBankAccountStateMachine.verify
                )
            ]
        ),

        TransitionTrigger(
            PayoutAccountStateMachine.reject,
            effects=[
                NotificationEffect(PayoutAccountRejected),
                RelatedTransitionEffect(
                    'external_accounts',
                    StripeBankAccountStateMachine.reject
                )
            ]
        )
    ]


def account_verified(effect):
    """connected payout account is verified"""
    return effect.instance.connect_account.status == PayoutAccountStateMachine.verified.value


@register(ExternalAccount)
class StripeBankAccountTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            StripeBankAccountStateMachine.verify,
            effects=[
                SubmitConnectedActivitiesEffect
            ]
        ),
        TransitionTrigger(
            StripeBankAccountStateMachine.initiate,
            effects=[
                TransitionEffect(
                    StripeBankAccountStateMachine.verify,
                    conditions=[
                        account_verified
                    ]
                )
            ]
        )
    ]
