from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger, register, TriggerManager
from bluebottle.funding.messages import PayoutAccountVerified, PayoutAccountRejected, LivePayoutAccountRejected
from bluebottle.funding.models import Funding
from bluebottle.funding.states import DonorStateMachine, PayoutAccountStateMachine
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
                RelatedTransitionEffect('donation', DonorStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            StripeSourcePaymentStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            StripeSourcePaymentStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            StripeSourcePaymentStateMachine.dispute,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.refund)
            ]
        ),
    ]


def has_live_campaign(effect):
    """has connected funding activity that is open"""
    live_statuses = ['open']
    return Funding.objects.filter(
        bank_account__connect_account=effect.instance
    ).filter(status__in=live_statuses).exists()


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
                NotificationEffect(
                    PayoutAccountRejected
                ),
                NotificationEffect(
                    LivePayoutAccountRejected,
                    conditions=[has_live_campaign]
                ),
                RelatedTransitionEffect(
                    'external_accounts',
                    StripeBankAccountStateMachine.reject
                )
            ]
        ),
    ]


def account_verified(effect):
    """connected payout account is verified"""
    return (
        effect.instance.connect_account and
        effect.instance.connect_account.status == PayoutAccountStateMachine.verified.value
    )


@register(ExternalAccount)
class StripeBankAccountTriggers(TriggerManager):
    triggers = [
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
