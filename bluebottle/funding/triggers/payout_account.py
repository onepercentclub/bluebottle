from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger, register, TriggerManager
)
from bluebottle.funding.effects import (
    SubmitPayoutEffect, SetDateEffect, DeleteDocumentEffect,
    ClearPayoutDatesEffect
)
from bluebottle.funding.messages.funding.activity_manager import (
    PayoutAccountVerified, PayoutAccountRejected
)
from bluebottle.funding.models import (
    PlainPayoutAccount, Payout, BankAccount
)
from bluebottle.funding.states import (
    PayoutStateMachine, BankAccountStateMachine, PlainPayoutAccountStateMachine
)
from bluebottle.notifications.effects import NotificationEffect


def is_reviewed(effect):
    """has been verified"""
    return effect.instance.reviewed


def is_unreviewed(effect):
    """has not been verified"""
    return not effect.instance.reviewed


@register(PlainPayoutAccount)
class PlainPayoutAccountTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            PlainPayoutAccountStateMachine.verify,
            effects=[
                NotificationEffect(PayoutAccountVerified),
                DeleteDocumentEffect
            ]
        ),

        TransitionTrigger(
            PlainPayoutAccountStateMachine.reject,
            effects=[
                NotificationEffect(PayoutAccountRejected),
                DeleteDocumentEffect
            ]
        ),
    ]


@register(BankAccount)
class BankAccountTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            BankAccountStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    'connect_account',
                    PlainPayoutAccountStateMachine.reject,
                    description='Reject connected KYC account'
                )
            ]
        ),
    ]


@register(Payout)
class PayoutTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            PayoutStateMachine.approve,
            effects=[
                SubmitPayoutEffect,
                SetDateEffect('date_approved')
            ]
        ),

        TransitionTrigger(
            PayoutStateMachine.start,
            effects=[
                SetDateEffect('date_started')
            ]
        ),

        TransitionTrigger(
            PayoutStateMachine.reset,
            effects=[
                ClearPayoutDatesEffect
            ]
        ),

        TransitionTrigger(
            PayoutStateMachine.schedule,
            effects=[
                ClearPayoutDatesEffect
            ]
        ),

        TransitionTrigger(
            PayoutStateMachine.succeed,
            effects=[
                SetDateEffect('date_completed')
            ]
        ),
    ]
