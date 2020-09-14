from bluebottle.fsm import triggers
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.activities.models import Activity, Contribution, Organizer

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine, OrganizerStateMachine
from bluebottle.activities.effects import CreateOrganizer

from bluebottle.initiatives.messages import (
    InitiativeRejectedOwnerMessage, InitiativeApprovedOwnerMessage,
    InitiativeCancelledOwnerMessage
)

from bluebottle.notifications.effects import NotificationEffect


def initiative_is_approved(effect):
    return effect.instance.initiative.status == 'approved'


@triggers.register(Activity)
class InitiateTrigger(triggers.TransitionTrigger):
    transition = ActivityStateMachine.initiate

    effects = [CreateOrganizer]


@triggers.register(Activity)
class SubmitTrigger(triggers.TransitionTrigger):
    transition = ActivityStateMachine.submit

    effects = [
        TransitionEffect('auto_approve', conditions=[initiative_is_approved])
    ]


@triggers.register(Activity)
class RejectTrigger(triggers.TransitionTrigger):
    transition = ActivityStateMachine.reject

    effects = [
        RelatedTransitionEffect('organizer', 'fail')
    ]


@triggers.register(Activity)
class CancelTrigger(triggers.TransitionTrigger):
    transition = ActivityStateMachine.cancel

    effects = [
        RelatedTransitionEffect('organizer', 'fail')
    ]


@triggers.register(Activity)
class RestoreTrigger(triggers.TransitionTrigger):
    transition = ActivityStateMachine.restore

    effects = [
        RelatedTransitionEffect('organizer', 'reset')
    ]


@triggers.register(Activity)
class DeleteTrigger(triggers.TransitionTrigger):
    transition = ActivityStateMachine.delete

    effects = [
        RelatedTransitionEffect('organizer', 'fail')
    ]
