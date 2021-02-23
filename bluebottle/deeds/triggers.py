from datetime import date
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers
)
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, ModelChangedTrigger
)
from bluebottle.deeds.states import (
    DeedStateMachine, ParticipantStateMachine
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
    has started
    """
    return (
        effect.instance.finished and
        effect.instance.start < date.today()
    )


def is_not_finished(effect):
    """
    hasn't started yet
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
    return effect.instace.start


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
            DeedStateMachine.start,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    ParticipantStateMachine.succeed,
                    conditions=[has_no_start_date]
                )
            ]
        ),

        TransitionTrigger(
            DeedStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'participants',
                    ParticipantStateMachine.succeed,
                )
            ]
        )
    ]


@register(DeedParticipant)
class ParticipantDeedTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + []
