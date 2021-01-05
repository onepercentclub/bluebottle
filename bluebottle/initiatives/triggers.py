from bluebottle.fsm.triggers import TransitionTrigger, TriggerManager, register
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.initiatives.states import ReviewStateMachine
from bluebottle.initiatives.models import Initiative
from bluebottle.activities.states import ActivityStateMachine
from bluebottle.time_based.states import TimeBasedStateMachine

from bluebottle.initiatives.messages import (
    InitiativeRejectedOwnerMessage, InitiativeApprovedOwnerMessage,
    InitiativeCancelledOwnerMessage
)

from bluebottle.notifications.effects import NotificationEffect


@register(Initiative)
class InitiativeTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            ReviewStateMachine.submit,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.auto_submit),
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.approve,
            effects=[
                RelatedTransitionEffect(
                    'activities',
                    ActivityStateMachine.auto_approve,
                ),
                NotificationEffect(InitiativeApprovedOwnerMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.reject,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.reject),
                NotificationEffect(InitiativeRejectedOwnerMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.cancel),
                RelatedTransitionEffect('activities', TimeBasedStateMachine.cancel),
                NotificationEffect(InitiativeCancelledOwnerMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.delete,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.delete),
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.restore,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.restore),
            ]
        ),
    ]
