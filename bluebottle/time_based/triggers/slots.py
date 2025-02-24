from django.utils.timezone import now

from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    register,
    TransitionTrigger,
    TriggerManager,
    ModelChangedTrigger,
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import ActiveTimeContributionsTransitionEffect, RescheduleDateSlotContributions
from bluebottle.time_based.effects.effects import (
    CreateNextSlotEffect,
    CreatePeriodicParticipantsEffect,
    RescheduleScheduleSlotContributions,
)
from bluebottle.time_based.effects.slots import (
    CreateTeamSlotParticipantsEffect, SetContributionsStartEffect
)
from bluebottle.time_based.messages import ChangedMultipleDateNotification, ChangedSingleDateNotification, SlotCancelledNotification
from bluebottle.time_based.models import PeriodicSlot, ScheduleSlot, TeamScheduleSlot
from bluebottle.time_based.notifications.teams import UserTeamDetailsChangedNotification
from bluebottle.time_based.states import (
    DateActivitySlotStateMachine,
    ScheduleSlotStateMachine,
    PeriodicParticipantStateMachine,
    ScheduleParticipantStateMachine,
    TeamScheduleSlotStateMachine,
    TeamStateMachine,
    PeriodicSlotStateMachine,
    TeamScheduleParticipantStateMachine,
    DateActivitySlot,
    TimeContributionStateMachine
)
from bluebottle.time_based.states.participants import DateParticipantStateMachine


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


def slot_is_full(effect):
    """
    Slot is full. Capacity is filled by participants.
    """
    participant_count = effect.instance.participants.filter(
        registration__status='accepted',
        status__in=['registered', 'succeeded']
    ).count()
    if effect.instance.capacity and participant_count >= effect.instance.capacity:
        return True
    return False


def slot_is_not_full(effect):
    """
    slot is not full. Still some spots available
    """
    return not slot_is_full(effect)


def has_accepted_participants(effect):
    """ has accepted participants"""
    return len(effect.instance.accepted_participants) > 0


def has_one_slot(effect):
    return effect.instance.activity.active_slots.count() == 1

def has_multiple_slots(effect):
    return effect.instance.activity.active_slots.count() > 1

def slot_is_started(effect):
    """
    slot start date/time has passed
    """
    return effect.instance.is_complete and effect.instance.start and effect.instance.start < now()


def slot_is_not_started(effect):
    """
    slot start date/time has not passed
    """
    return not slot_is_started(effect)


@register(DateActivitySlot)
class DateActivitySlotTriggers(TriggerManager):

    triggers = [
        TransitionTrigger(
            DateActivitySlotStateMachine.initiate,
            effects=[
                TransitionEffect(
                    DateActivitySlotStateMachine.mark_complete,
                    conditions=[slot_is_complete]
                ),
                TransitionEffect(
                    DateActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),
            ],
        ),
        ModelChangedTrigger(
            "start",
            effects=[
                RescheduleScheduleSlotContributions,
                TransitionEffect(
                    DateActivitySlotStateMachine.finish, conditions=[slot_is_finished]
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
            DateActivitySlotStateMachine.finish,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed),
                RelatedTransitionEffect(
                    "participants",
                    DateParticipantStateMachine.succeed,
                ),
            ],
        ),
        TransitionTrigger(
            DateActivitySlotStateMachine.cancel,
            effects=[
                NotificationEffect(SlotCancelledNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail),
                RelatedTransitionEffect(
                    "participants",
                    DateParticipantStateMachine.cancel,
                ),
            ],
        ),
        TransitionTrigger(
            DateActivitySlotStateMachine.restore,
            effects=[
                TransitionEffect(
                    DateActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset)
            ],
        ),
        TransitionTrigger(
            DateActivitySlotStateMachine.reschedule,
            effects=[
                TransitionEffect(
                    DateActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset),
                TransitionEffect(
                    DateActivitySlotStateMachine.lock,
                    conditions=[slot_is_full]
                ),
            ],
        ),
        ModelChangedTrigger(
            ['start', 'duration', 'is_online', 'location_id', 'location_hint'],
            effects=[
                TransitionEffect(
                    DateActivitySlotStateMachine.mark_complete,
                    conditions=[slot_is_complete]
                ),
                TransitionEffect(
                    DateActivitySlotStateMachine.mark_incomplete,
                    conditions=[slot_is_incomplete]
                ),
                NotificationEffect(
                    ChangedSingleDateNotification,
                    conditions=[
                        has_accepted_participants,
                        slot_is_not_finished,
                        has_one_slot
                    ]
                ),
                NotificationEffect(
                    ChangedMultipleDateNotification,
                    conditions=[
                        has_accepted_participants,
                        slot_is_not_finished,
                        has_multiple_slots
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'start',
            effects=[
                RescheduleDateSlotContributions,
                TransitionEffect(
                    DateActivitySlotStateMachine.start,
                    conditions=[slot_is_started, slot_is_not_finished]
                ),

                TransitionEffect(
                    DateActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),

                TransitionEffect(
                    DateActivitySlotStateMachine.reschedule,
                    conditions=[slot_is_not_started]
                ),
            ]
        ),

        ModelChangedTrigger(
            'duration',
            effects=[
                RescheduleDateSlotContributions,
            ]
        ),

        ModelChangedTrigger(
            'capacity',
            effects=[
                TransitionEffect(
                    DateActivitySlotStateMachine.lock,
                    conditions=[slot_is_full]
                ),

                TransitionEffect(
                    DateActivitySlotStateMachine.unlock,
                    conditions=[slot_is_not_full]
                ),
            ]
        ),

    ]