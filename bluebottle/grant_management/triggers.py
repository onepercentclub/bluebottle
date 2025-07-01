from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import ActivityTriggers
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    ModelChangedTrigger, TransitionTrigger, register, TriggerManager
)
from bluebottle.funding.effects import (
    SubmitPayoutEffect, SetDateEffect, ClearPayoutDatesEffect
)
from bluebottle.grant_management.messages.activity_manager import GrantApplicationApprovedMessage, \
    GrantApplicationNeedsWorkMessage, GrantApplicationRejectedMessage, GrantApplicationCancelledMessage, \
    GrantApplicationSubmittedMessage
from bluebottle.grant_management.models import (
    GrantDeposit,
    GrantDonor, GrantApplication,
    GrantPayout
)
from bluebottle.grant_management.states import (
    LedgerItemStateMachine, GrantDepositStateMachine,
    GrantDonorStateMachine, GrantApplicationStateMachine,
    GrantPayoutStateMachine
)
from bluebottle.notifications.effects import NotificationEffect


def has_reference(effect):
    return bool(effect.instance.reference)


@register(GrantDeposit)
class GrantDepositTriggers(TriggerManager):
    triggers = [
        ModelChangedTrigger(
            ['reference'],
            effects=[
                TransitionEffect(GrantDepositStateMachine.complete, conditions=[has_reference])
            ]
        ),
        TransitionTrigger(
            GrantDepositStateMachine.complete,
            effects=[
                RelatedTransitionEffect('ledger_items', LedgerItemStateMachine.finalise)

            ]
        ),
    ]


@register(GrantDonor)
class GrantDonorTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            GrantDonorStateMachine.initiate,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    GrantApplicationStateMachine.approve
                ),
            ]
        ),
    ]


@register(GrantApplication)
class GrantApplicationTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [

        TransitionTrigger(
            GrantApplicationStateMachine.approve,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed),
                NotificationEffect(
                    GrantApplicationApprovedMessage
                )
            ]
        ),
        TransitionTrigger(
            GrantApplicationStateMachine.submit,
            effects=[
                NotificationEffect(
                    GrantApplicationSubmittedMessage
                )
            ]
        ),
        TransitionTrigger(
            GrantApplicationStateMachine.request_changes,
            effects=[
                NotificationEffect(
                    GrantApplicationNeedsWorkMessage
                )
            ]
        ),
        TransitionTrigger(
            GrantApplicationStateMachine.reject,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(
                    GrantApplicationRejectedMessage
                )
            ]
        ),
        TransitionTrigger(
            GrantApplicationStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                NotificationEffect(
                    GrantApplicationCancelledMessage
                )
            ]
        ),
    ]


@register(GrantPayout)
class GrantPayoutTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            GrantPayoutStateMachine.approve,
            effects=[
                SubmitPayoutEffect,
                SetDateEffect('date_approved')
            ]
        ),

        TransitionTrigger(
            GrantPayoutStateMachine.start,
            effects=[
                SetDateEffect('date_started')
            ]
        ),

        TransitionTrigger(
            GrantPayoutStateMachine.reset,
            effects=[
                ClearPayoutDatesEffect
            ]
        ),

        TransitionTrigger(
            GrantPayoutStateMachine.schedule,
            effects=[
                ClearPayoutDatesEffect
            ]
        ),

        TransitionTrigger(
            GrantPayoutStateMachine.succeed,
            effects=[
                SetDateEffect('date_completed')
            ]
        ),
    ]
