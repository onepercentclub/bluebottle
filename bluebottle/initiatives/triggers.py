from bluebottle.fsm.triggers import TransitionTrigger, TriggerManager, register
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.initiatives.states import ReviewStateMachine
from bluebottle.initiatives.models import Initiative
from bluebottle.activities.states import ActivityStateMachine
from bluebottle.assignments.states import AssignmentStateMachine
from bluebottle.funding.states import FundingStateMachine
from bluebottle.events.states import EventStateMachine

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
                RelatedTransitionEffect('activities', AssignmentStateMachine.auto_approve),
                RelatedTransitionEffect('activities', EventStateMachine.auto_approve),
                NotificationEffect(InitiativeApprovedOwnerMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.reject,
            effects=[
                RelatedTransitionEffect('activities', AssignmentStateMachine.reject),
                RelatedTransitionEffect('activities', EventStateMachine.reject),
                RelatedTransitionEffect('activities', FundingStateMachine.reject),
                NotificationEffect(InitiativeRejectedOwnerMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('activities', AssignmentStateMachine.cancel),
                RelatedTransitionEffect('activities', EventStateMachine.cancel),
                RelatedTransitionEffect('activities', FundingStateMachine.cancel),
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
                RelatedTransitionEffect('activities', AssignmentStateMachine.restore),
                RelatedTransitionEffect('activities', EventStateMachine.restore),
                RelatedTransitionEffect('activities', FundingStateMachine.restore),
            ]
        ),
    ]
