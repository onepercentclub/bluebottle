from django.utils.timezone import now

from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register,
    TransitionTrigger,
    TriggerManager,
    ModelChangedTrigger,
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects.effects import (
    CreateNextSlotEffect,
    CreatePeriodicParticipantsEffect,
    RescheduleScheduleSlotContributions,
)
from bluebottle.time_based.effects.slots import (
    CreateTeamSlotParticipantsEffect, SetContributionsStartEffect
)
from bluebottle.time_based.models import PeriodicSlot, ScheduleSlot, TeamScheduleSlot
from bluebottle.time_based.notifications.teams import UserTeamDetailsChangedNotification
from bluebottle.time_based.states import (
    ScheduleSlotStateMachine,
    PeriodicParticipantStateMachine,
    ScheduleParticipantStateMachine,
    TeamScheduleSlotStateMachine,
    TeamStateMachine,
    PeriodicSlotStateMachine,
    TeamScheduleParticipantStateMachine,
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


def slot_is_finished(effect):
    return effect.instance.end and effect.instance.end < now()


def slot_is_not_finished(effect):
    return effect.instance.end and effect.instance.end > now()


def slot_is_scheduled(effect):
    return effect.instance.end


def slot_has_no_end(effect):
    return not effect.instance.end


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
                    ScheduleSlotStateMachine.unschedule, conditions=[slot_has_no_end]
                ),
                TransitionEffect(
                    ScheduleSlotStateMachine.schedule, conditions=[slot_is_scheduled, slot_is_not_finished]
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
                SetContributionsStartEffect,
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.succeed,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleSlotStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.cancel,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleSlotStateMachine.restore,
            effects=[
                TransitionEffect(
                    ScheduleSlotStateMachine.finish, conditions=[slot_is_finished]
                ),
                TransitionEffect(
                    ScheduleSlotStateMachine.unschedule, conditions=[slot_has_no_end]
                ),
                TransitionEffect(
                    ScheduleSlotStateMachine.schedule, conditions=[slot_is_scheduled, slot_is_not_finished]
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleSlotStateMachine.schedule,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.schedule,
                ),
                RelatedTransitionEffect(
                    "team",
                    TeamStateMachine.schedule,
                ),
            ],
        ),
        TransitionTrigger(
            ScheduleSlotStateMachine.unschedule,
            effects=[
                RelatedTransitionEffect(
                    "participants",
                    ScheduleParticipantStateMachine.unschedule,
                ),
                RelatedTransitionEffect(
                    "team",
                    TeamStateMachine.unschedule,
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
            ScheduleSlotStateMachine.finish,
            effects=[
                RelatedTransitionEffect("team", TeamStateMachine.succeed),
            ],
        ),
        TransitionTrigger(
            ScheduleSlotStateMachine.schedule,
            effects=[
                RelatedTransitionEffect("participants", TeamScheduleParticipantStateMachine.schedule),
                RelatedTransitionEffect("team", TeamStateMachine.schedule),
                RelatedTransitionEffect(
                    "participants", TeamScheduleParticipantStateMachine.schedule
                ),
            ],
        ),
        ModelChangedTrigger(
            ["start", "duration", "location_id", "is_online"],
            effects=[
                TransitionEffect(
                    TeamScheduleSlotStateMachine.schedule,
                    conditions=[slot_is_complete, slot_is_not_finished],
                ),
                TransitionEffect(
                    TeamScheduleSlotStateMachine.unschedule, conditions=[slot_is_incomplete]
                ),
                TransitionEffect(
                    TeamScheduleSlotStateMachine.finish, conditions=[slot_is_finished]
                ),
                NotificationEffect(
                    UserTeamDetailsChangedNotification, conditions=[slot_is_scheduled]
                ),
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
    ]
