from django.utils.timezone import now
from bluebottle.time_based.states import TeamStateMachine

from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register,
    TransitionTrigger,
    TriggerManager,
    ModelChangedTrigger,
)
from bluebottle.time_based.effects.effects import (
    CreateNextSlotEffect,
    CreatePeriodicParticipantsEffect,
    RescheduleScheduleSlotContributions,
)
from bluebottle.time_based.effects.slots import (
    CreateTeamSlotParticipantsEffect
)
from bluebottle.time_based.models import PeriodicSlot, ScheduleSlot, TeamScheduleSlot
from bluebottle.time_based.states import (
    PeriodicSlotStateMachine,
    ScheduleSlotStateMachine,
)
from bluebottle.time_based.states.participants import (
    PeriodicParticipantStateMachine,
    ScheduleParticipantStateMachine,
    TeamScheduleParticipantStateMachine,
)
from bluebottle.time_based.states.states import TeamScheduleSlotStateMachine


@register(PeriodicSlot)
class PeriodicSlotTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            PeriodicSlotStateMachine.initiate,
            effects=[
                CreatePeriodicParticipantsEffect,
            ]
        ),
        TransitionTrigger(
            PeriodicSlotStateMachine.finish,
            effects=[
                CreateNextSlotEffect,
                RelatedTransitionEffect(
                    'participants',
                    PeriodicParticipantStateMachine.succeed,
                ),
            ]
        ),
    ]


def slot_is_finished(effect):
    return effect.instance.end and effect.instance.end < now()


def slot_is_not_finished(effect):
    return not effect.instance.end or effect.instance.end > now()


@register(ScheduleSlot)
class ScheduleSlotTriggers(TriggerManager):

    triggers = [
        TransitionTrigger(
            ScheduleSlotStateMachine.initiate,
            effects=[
                TransitionEffect(
                    ScheduleSlotStateMachine.finish, conditions=[slot_is_finished]
                ),
            ],
        ),
        ModelChangedTrigger(
            "start",
            effects=[
                RescheduleScheduleSlotContributions,
                TransitionEffect(
                    ScheduleSlotStateMachine.finish, conditions=[slot_is_finished]
                ),
                TransitionEffect(
                    ScheduleSlotStateMachine.reopen, conditions=[slot_is_not_finished]
                ),
            ],
        ),
        ModelChangedTrigger(
            "duration",
            effects=[
                RescheduleScheduleSlotContributions,
            ],
        ),
        TransitionTrigger(
            ScheduleSlotStateMachine.finish,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.succeed,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleSlotStateMachine.reopen,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.reset,
                ),
            ],
        ),
    ]


def slot_is_complete(effect):
    return (
        effect.instance.start
        and effect.instance.duration
        and (effect.instance.is_online is True or effect.instance.location)
    )


def slot_is_incomplete(effect):
    return not slot_is_complete(effect)


@register(TeamScheduleSlot)
class TeamScheduleSlotTriggers(ScheduleSlotTriggers):

    triggers = ScheduleSlotTriggers.triggers + [
        TransitionTrigger(
            ScheduleSlotStateMachine.initiate,
            effects=[
                CreateTeamSlotParticipantsEffect,
            ],
        ),
        TransitionTrigger(
            ScheduleSlotStateMachine.schedule,
            effects=[
                RelatedTransitionEffect("team", TeamStateMachine.schedule),
                RelatedTransitionEffect(
                    "participants", TeamScheduleParticipantStateMachine.schedule
                ),
            ],
        ),
        ModelChangedTrigger(
            ["start", "end", "location", "is_online"],
            effects=[
                TransitionEffect(
                    TeamScheduleSlotStateMachine.schedule,
                    conditions=[slot_is_complete, slot_is_not_finished],
                ),
                TransitionEffect(
                    TeamScheduleSlotStateMachine.reset, conditions=[slot_is_incomplete]
                ),
                TransitionEffect(
                    TeamScheduleSlotStateMachine.finish, conditions=[slot_is_finished]
                )
            ],
        ),
        TransitionTrigger(
            TeamScheduleSlotStateMachine.finish,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    TeamScheduleParticipantStateMachine.succeed,
                ),
            ],
        ),
        ModelChangedTrigger(
            "start",
            effects=[
                RescheduleScheduleSlotContributions,
                TransitionEffect(
                    TeamScheduleSlotStateMachine.finish, conditions=[slot_is_finished]
                ),
                TransitionEffect(
                    TeamScheduleSlotStateMachine.reopen,
                    conditions=[slot_is_not_finished],
                ),
            ],
        ),
    ]
