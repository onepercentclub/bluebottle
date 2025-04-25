from bluebottle.activities.effects import SetPublishedDateEffect
from bluebottle.activities.states import ActivityStateMachine
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.triggers import TransitionTrigger, TriggerManager, register, ModelChangedTrigger
from bluebottle.initiatives.messages.initiator import InitiativeApprovedInitiatorMessage, \
    InitiativeRejectedInitiatorMessage, InitiativeCancelledInitiatorMessage, InitiativePublishedInitiatorMessage, \
    InitiativeSubmittedInitiatorMessage
from bluebottle.initiatives.messages.reviewer import InitiativeSubmittedReviewerMessage, AssignedReviewerMessage, \
    InitiativePublishedReviewerMessage
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.states import ReviewStateMachine
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.states import TimeBasedStateMachine, DateStateMachine


def reviewer_is_set(effect):
    return effect.instance.reviewer is not None


@register(Initiative)
class InitiativeTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            ReviewStateMachine.submit,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.auto_submit),
                NotificationEffect(InitiativeSubmittedReviewerMessage),
                NotificationEffect(InitiativeSubmittedInitiatorMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.publish,
            effects=[
                SetPublishedDateEffect,
                NotificationEffect(InitiativePublishedInitiatorMessage),
                NotificationEffect(InitiativePublishedReviewerMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.approve,
            effects=[
                SetPublishedDateEffect,
                RelatedTransitionEffect(
                    'activities',
                    ActivityStateMachine.auto_approve,
                ),
                RelatedTransitionEffect(
                    'activities',
                    DateStateMachine.auto_publish,
                ),
                NotificationEffect(InitiativeApprovedInitiatorMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.reject,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.reject),
                NotificationEffect(InitiativeRejectedInitiatorMessage)
            ]
        ),

        TransitionTrigger(
            ReviewStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('activities', ActivityStateMachine.cancel),
                RelatedTransitionEffect('activities', TimeBasedStateMachine.cancel),
                NotificationEffect(InitiativeCancelledInitiatorMessage)
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
