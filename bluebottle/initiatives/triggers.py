from bluebottle.fsm import triggers
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
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


@triggers.register(Initiative)
class SubmitTrigger(triggers.TransitionTrigger):
    transition = ReviewStateMachine.submit

    effects = [
        RelatedTransitionEffect('activities', ActivityStateMachine.auto_submit),
    ]


@triggers.register(Initiative)
class ApproveTrigger(triggers.TransitionTrigger):
    transition = ReviewStateMachine.approve

    effects = [
        RelatedTransitionEffect('activities', AssignmentStateMachine.auto_approve),
        RelatedTransitionEffect('activities', EventStateMachine.auto_approve),
        NotificationEffect(InitiativeApprovedOwnerMessage)
    ]


@triggers.register(Initiative)
class RejectTrigger(triggers.TransitionTrigger):
    transition = ReviewStateMachine.reject

    effects = [
        RelatedTransitionEffect('activities', AssignmentStateMachine.reject),
        RelatedTransitionEffect('activities', EventStateMachine.reject),
        RelatedTransitionEffect('activities', FundingStateMachine.reject),
        NotificationEffect(InitiativeRejectedOwnerMessage)
    ]


@triggers.register(Initiative)
class CancelTrigger(triggers.TransitionTrigger):
    transition = ReviewStateMachine.cancel

    effects = [
        RelatedTransitionEffect('activities', AssignmentStateMachine.cancel),
        RelatedTransitionEffect('activities', EventStateMachine.cancel),
        RelatedTransitionEffect('activities', FundingStateMachine.cancel),
        NotificationEffect(InitiativeCancelledOwnerMessage)
    ]


@triggers.register(Initiative)
class DeleteTrigger(triggers.TransitionTrigger):
    transition = ReviewStateMachine.delete

    effects = [
        RelatedTransitionEffect('activities', ActivityStateMachine.delete),
    ]


@triggers.register(Initiative)
class RestoreTrigger(triggers.TransitionTrigger):
    transition = ReviewStateMachine.restore

    effects = [
        RelatedTransitionEffect('activities', AssignmentStateMachine.restore),
        RelatedTransitionEffect('activities', EventStateMachine.restore),
        RelatedTransitionEffect('activities', FundingStateMachine.restore),
    ]
