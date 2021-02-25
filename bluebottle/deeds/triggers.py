from datetime import date

from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers
)
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.deeds.states import (
    DeedStateMachine, ParticipantStateMachine
)
from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, ModelChangedTrigger
)


def is_started(effect):
    """
    has started
    """
    return (
        effect.instance.start and
        effect.instance.start < date.today()
    )


def is_not_started(effect):
    """
    hasn't started yet
    """
    return not is_started(effect)


def is_finished(effect):
    """
    has finished
    """
    return (
        effect.instance.end and
        effect.instance.end < date.today()
    )


def is_not_finished(effect):
    """
    hasn't finished yet
    """
    return not is_finished(effect)


def has_participants(effect):
    """ has participants"""
    return len(effect.instance.participants) > 0


def has_no_participants(effect):
    """ has accepted participants"""
    return not has_participants(effect)


def has_no_start_date(effect):
    """ has accepted participants"""
    return not effect.instance.start


@register(Deed)
class DeedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger('start', effects=[TransitionEffect(DeedStateMachine.start)]),
        ModelChangedTrigger(
            'end',
            effects=[
                TransitionEffect(DeedStateMachine.restart, conditions=[is_started]),
                TransitionEffect(DeedStateMachine.reopen, conditions=[is_not_started]),
                TransitionEffect(DeedStateMachine.succeed, conditions=[is_finished, has_participants]),
                TransitionEffect(DeedStateMachine.expire, conditions=[is_finished, has_no_participants]),
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                TransitionEffect(DeedStateMachine.start, conditions=[is_started]),
                TransitionEffect(DeedStateMachine.reopen, conditions=[is_not_started]),
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.expire,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
            ]
        ),

    ]


def activity_is_finished(effect):
    """activity is finished"""
    return (
        effect.instance.activity.end and
        effect.instance.activity.end < date.today()
    )


def activity_will_be_empty(effect):
    """activity will be empty"""
    return len(effect.instance.activity.participants) == 1


@register(DeedParticipant)
class DeedParticipantTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.remove,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeedStateMachine.expire,
                    conditions=[activity_is_finished, activity_will_be_empty]
                ),
            ]
        ),
        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    DeedStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),
            ]
        ),

    ]
