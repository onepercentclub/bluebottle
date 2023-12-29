from bluebottle.activities.states import ActivityStateMachine
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger, TriggerManager, register, ModelChangedTrigger
from bluebottle.initiatives.messages import (
    InitiativeRejectedOwnerMessage, InitiativeApprovedOwnerMessage,
    InitiativeCancelledOwnerMessage, AssignedReviewerMessage, InitiativeSubmittedStaffMessage
)
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.states import ReviewStateMachine
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.states import DateStateMachine, TimeBasedStateMachine


def reviewer_is_set(effect):
    return effect.instance.reviewer is not None


@register(Initiative)
class InitiativeTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            ReviewStateMachine.submit,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.auto_submit),
                NotificationEffect(InitiativeSubmittedStaffMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.approve,
            effects=[
                RelatedTransitionEffect(
                    'activities',
                    ActivityStateMachine.auto_approve,
                ),
                RelatedTransitionEffect(
                    'activities',
                    DateStateMachine.auto_publish,
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
        ModelChangedTrigger(
            'reviewer_id',
            effects=[
                NotificationEffect(AssignedReviewerMessage)
            ]
        ),
    ]
