from django.utils.timezone import now

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
)


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


@register(ScheduleSlot)
class ScheduleSlotTriggers(TriggerManager):

    def slot_is_finished(effect):
        return effect.instance.end and effect.instance.end < now()

    def slot_is_not_finished(effect):
        return not effect.instance.end or effect.instance.end > now()

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


@register(TeamScheduleSlot)
class TeamScheduleSlotTriggers(ScheduleSlotTriggers):
    triggers = ScheduleSlotTriggers.triggers + [
        TransitionTrigger(
            ScheduleSlotStateMachine.initiate,
            effects=[
                CreateTeamSlotParticipantsEffect,
            ],
        ),
    ]
