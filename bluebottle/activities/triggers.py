from bluebottle.fsm.triggers import TriggerManager, TransitionTrigger
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect

from bluebottle.activities.states import ActivityStateMachine, OrganizerStateMachine
from bluebottle.activities.effects import CreateOrganizer


def initiative_is_approved(effect):
    return effect.instance.initiative.status == 'approved'


class ActivityTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(ActivityStateMachine.initiate, effects=[CreateOrganizer]),

        TransitionTrigger(
            ActivityStateMachine.submit,
            effects=[
                TransitionEffect(
                    ActivityStateMachine.auto_approve,
                    conditions=[initiative_is_approved]
                )
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.reject,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.auto_approve,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed),
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.expire,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.restore,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.reset)
            ]
        ),

        TransitionTrigger(
            ActivityStateMachine.delete,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail)
            ]
        ),
    ]


class ContributorTriggers(TriggerManager):
    triggers = []


class ContributionValueTriggers(TriggerManager):
    triggers = []
