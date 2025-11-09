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
    CreateTeamSlotParticipantsEffect, SetContributionsStartEffect, LockActivityEffect
)
from bluebottle.time_based.messages import (
    ChangedMultipleDateNotification, ChangedSingleDateNotification, SlotCancelledNotification
)
from bluebottle.time_based.messages.teams import UserTeamDetailsChangedNotification
from bluebottle.time_based.models import PeriodicSlot, ScheduleSlot, TeamScheduleSlot
from bluebottle.time_based.states import (
    DateStateMachine,
    DateActivitySlotStateMachine,
    ScheduleSlotStateMachine,
    PeriodicParticipantStateMachine,
    ScheduleParticipantStateMachine,
    TeamScheduleSlotStateMachine,
    TeamStateMachine,
    PeriodicSlotStateMachine,
    TeamScheduleParticipantStateMachine,
    DateActivitySlot,
    TimeContributionStateMachine, ParticipantStateMachine
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
    """
    Slot is finished. The end date/time has passed.
    """
    return effect.instance.end and effect.instance.end < now()


def slot_has_started(effect):
    """
    Slot has started. The start date/time has passed.
    """
    return not effect.instance.start or effect.instance.start < now()


def slot_has_not_started(effect):
    """
    Slot has not started. The start date/time has not passed.
    """
    return effect.instance.start and effect.instance.start > now()


def slot_is_not_finished(effect):
    """
    Slot is not finished. The end date/time has not passed.
    """
    return effect.instance.end and effect.instance.end > now()


def slot_is_scheduled(effect):
    """
    Slot is scheduled. It has a start date/time and a duration.
    """
    return effect.instance.end


def slot_has_no_end(effect):
    """
    Slot has no end date/time.
    """
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
            ScheduleSlotStateMachine.auto_cancel,
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
    return bool(
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
        status__in=['accepted', 'succeeded']
    ).count()
    if effect.instance.capacity and participant_count >= effect.instance.capacity:
        return True
    return False


def slot_has_participants(effect):
    """
    Slot is full. Capacity is filled by participants.
    """
    return effect.instance.pk and effect.instance.participants.filter(
        status__in=['accepted', 'succeeded']
    ).count() > 0


def slot_has_no_participants(effect):
    """
    Slot is full. Capacity is filled by participants.
    """
    return not slot_has_participants(effect)


def slot_is_not_full(effect):
    """
    slot is not full. Still some spots available
    """
    return not slot_is_full(effect)


def has_accepted_participants(effect):
    """ has accepted participants"""
    return len(effect.instance.accepted_participants) > 0


def has_one_slot(effect):
    """
    Has only one slot
    """
    return effect.instance.activity.active_slots.count() == 1


def has_multiple_slots(effect):
    """
    Has multiple slots
    """
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


def activity_has_no_open_slot(effect):
    """
    activity has no open slots. All slots are either finished or full
    """
    return len(
        effect.instance.activity.slots.exclude(pk=effect.instance.pk).filter(status='open')
    ) == 0


def all_upcoming_slots_full(effect):
    upcoming_slots = effect.instance.activity.slots.exclude(
        id=effect.instance.id
    ).filter(
        status__in=['open', 'full']
    ).filter(start__gte=now())
    return upcoming_slots.count() and upcoming_slots.count() == upcoming_slots.filter(status='full').count()


def activity_has_finished_slot(effect):
    """
    activity has finished slots. All slots are either finished or full
    """
    return len(
        effect.instance.activity.slots.filter(status='finished')
    ) > 0


def activity_has_open_slots(effect):
    """
    activity has open slots. At least one slot is still open
    """
    return effect.instance.activity.slots.exclude(pk=effect.instance.pk).filter(status='open').count()


def activity_has_succeeded_slots(effect):
    """
    activity has succeeded slots. At least one slot is succeeded
    """
    return effect.instance.activity.slots.exclude(
        pk=effect.instance.pk
    ).filter(status='finished').count() > 0


def activity_has_no_upcoming_slots(effect):
    """
    activity has no open slots. All slots are either finished or full
    """
    return effect.instance.activity.slots.exclude(
        pk=effect.instance.pk
    ).filter(status__in=['open', 'full']).count() == 0


def activity_is_finished(effect):
    """
    activity is finished. All slots are either finished or full
    """
    if effect.instance.start and effect.instance.start > now():
        return False
    result = (
        effect.instance.activity.slots.exclude(
            pk=effect.instance.pk
        ).filter(
            status__in=['open', 'full']
        ).count() == 0
    )
    return result


def activity_is_not_finished(effect):
    """
    activity is not finished.
    """
    return not activity_is_finished(effect)


def activity_has_participants(effect):
    """
    Activity has accepted participants.
    """
    return effect.instance.activity.participants.count() > 0


def activity_has_no_participants(effect):
    """
    Activity has no accepted participants.
    """
    return not activity_has_participants(effect)


def all_slots_cancelled(effect):
    """
    all slots are cancelled
    """
    return effect.instance.activity.slots.exclude(
        status__in=['cancelled', 'deleted', 'expired']
    ).exclude(id=effect.instance.id).count() == 0


@register(DateActivitySlot)
class DateActivitySlotTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            DateActivitySlotStateMachine.initiate,
            effects=[
                TransitionEffect(
                    DateActivitySlotStateMachine.mark_complete,
                    conditions=[
                        slot_is_complete,
                    ]
                ),
            ],
        ),

        TransitionTrigger(
            DateActivitySlotStateMachine.mark_complete,
            effects=[
                TransitionEffect(
                    DateActivitySlotStateMachine.finish,
                    conditions=[
                        slot_is_finished
                    ]
                ),
                TransitionEffect(
                    DateActivitySlotStateMachine.start,
                    conditions=[
                        slot_has_started,
                        slot_is_not_finished
                    ]
                ),
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.reopen,
                    conditions=[
                        slot_has_not_started
                    ]
                ),
            ],
        ),

        TransitionTrigger(
            DateActivitySlotStateMachine.lock,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.lock,
                    conditions=[activity_has_no_open_slot]
                ),
                LockActivityEffect
            ],
        ),

        TransitionTrigger(
            DateActivitySlotStateMachine.unlock,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.reopen,
                ),
            ],
        ),

        TransitionTrigger(
            DateActivitySlotStateMachine.start,
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.lock,
                    conditions=[activity_has_no_open_slot]
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
                RelatedTransitionEffect(
                    "active_and_new_participants",
                    DateParticipantStateMachine.succeed
                ),
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.succeed,
                    conditions=[
                        activity_is_finished,
                        activity_has_participants
                    ]
                ),
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.expire,
                    conditions=[
                        activity_is_finished,
                        activity_has_no_participants
                    ]
                ),
            ],
        ),
        TransitionTrigger(
            DateActivitySlotStateMachine.cancel,
            effects=[
                NotificationEffect(SlotCancelledNotification),
                RelatedTransitionEffect(
                    "participants",
                    ParticipantStateMachine.cancel,
                ),

                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.lock,
                    conditions=[
                        all_upcoming_slots_full
                    ]
                ),
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.succeed,
                    conditions=[
                        activity_has_no_upcoming_slots,
                        activity_has_succeeded_slots
                    ]
                ),
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.cancel,
                    conditions=[all_slots_cancelled]
                ),
            ],
        ),
        TransitionTrigger(
            DateActivitySlotStateMachine.auto_cancel,
            effects=[
                NotificationEffect(SlotCancelledNotification),
                RelatedTransitionEffect(
                    "participants",
                    ParticipantStateMachine.cancel,
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
                TransitionEffect(
                    DateActivitySlotStateMachine.lock,
                    conditions=[slot_is_full]
                ),
                RelatedTransitionEffect(
                    'activity',
                    DateStateMachine.reopen,
                    conditions=[activity_is_not_finished]
                ),
                RelatedTransitionEffect(
                    'participants',
                    DateParticipantStateMachine.restore,
                    conditions=[slot_is_not_finished]
                ),
                RelatedTransitionEffect(
                    'participants',
                    DateParticipantStateMachine.succeed,
                    conditions=[slot_is_finished]
                )
            ],
        ),
        TransitionTrigger(
            DateActivitySlotStateMachine.reschedule,
            effects=[
                TransitionEffect(
                    DateActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),
                TransitionEffect(
                    DateActivitySlotStateMachine.start,
                    conditions=[
                        slot_is_started,
                        slot_is_not_finished
                    ]
                ),
                TransitionEffect(
                    DateActivitySlotStateMachine.lock,
                    conditions=[slot_is_full]
                ),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset),
                RelatedTransitionEffect(
                    'activity',
                    DateStateMachine.reopen
                )
            ],
        ),
        ModelChangedTrigger(
            ['start', 'duration', 'is_online', 'location_id', 'location_hint'],
            effects=[
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.succeed,
                    conditions=[activity_is_finished, activity_has_participants]
                ),
                RelatedTransitionEffect(
                    "activity",
                    DateStateMachine.expire,
                    conditions=[activity_is_finished, activity_has_no_participants]
                ),
                TransitionEffect(
                    DateActivitySlotStateMachine.mark_complete,
                    conditions=[
                        slot_is_complete,
                    ]
                ),
                TransitionEffect(
                    DateActivitySlotStateMachine.start,
                    conditions=[
                        slot_is_started,
                        slot_is_not_finished
                    ]
                ),
                TransitionEffect(
                    DateActivitySlotStateMachine.finish,
                    conditions=[
                        slot_is_finished
                    ]
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
                    conditions=[
                        slot_is_started,
                        slot_is_not_finished
                    ]
                ),

                TransitionEffect(
                    DateActivitySlotStateMachine.finish,
                    conditions=[slot_is_finished]
                ),

                TransitionEffect(
                    DateActivitySlotStateMachine.reschedule,
                    conditions=[
                        slot_is_not_started
                    ]
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
