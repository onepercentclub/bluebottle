from datetime import date

from django.utils.timezone import now

from bluebottle.activities.messages import (
    ActivityCancelledNotification,
    ActivityExpiredNotification,
    ActivityRejectedNotification,
    ActivityRestoredNotification,
    ActivitySucceededNotification,
)
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import ActivityTriggers, has_organizer
from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger, TransitionTrigger, register
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import (
    ActiveTimeContributionsTransitionEffect,
    CreateFirstSlotEffect,
)
from bluebottle.time_based.effects.contributions import (
    RescheduleActivityDurationsEffect,
)
from bluebottle.time_based.models import (
    DateActivity,
    DateActivitySlot,
    DeadlineActivity,
    PeriodicActivity,
    ScheduleActivity,
)
from bluebottle.time_based.states import (
    DateStateMachine,
    ParticipantStateMachine,
    ScheduleActivityStateMachine,
    TimeContributionStateMachine,
)
from bluebottle.time_based.states.participants import (
    RegistrationParticipantStateMachine,
    ScheduleParticipantStateMachine,
)
from bluebottle.time_based.states.states import (
    RegistrationActivityStateMachine,
    PeriodicActivityStateMachine,
    ScheduleActivityStateMachine,
    ScheduleSlotStateMachine,
)


def is_full(effect):
    """
    the activity is full
    """
    if getattr(effect.instance, "team_activity", None) == "teams":
        accepted_teams = effect.instance.teams.filter(
            status__in=["open", "running", "finished"]
        ).count()
        return effect.instance.capacity and effect.instance.capacity <= accepted_teams

    if isinstance(effect.instance, DateActivity) and effect.instance.slots.count() > 1:
        return False

    return effect.instance.capacity and effect.instance.capacity <= len(
        effect.instance.accepted_participants
    )


def is_not_full(effect):
    """
    the activity is not full
    """
    if getattr(effect.instance, "team_activity", None) == "teams":
        accepted_teams = effect.instance.teams.filter(
            status__in=["open", "running", "finished"]
        ).count()
        return not effect.instance.capacity or effect.instance.capacity > accepted_teams

    return not effect.instance.capacity or effect.instance.capacity > len(
        effect.instance.accepted_participants
    )


def has_participants(effect):
    """has participants"""
    return len(effect.instance.active_participants) > 0


def has_no_participants(effect):
    """
    has no participants
    """
    return len(effect.instance.active_participants) == 0


def is_finished(effect):
    """
    is finished
    """
    if isinstance(effect.instance, DateActivitySlot):
        slot = effect.instance
    else:
        slot = effect.instance.slots.order_by("start").last()
    return slot and slot.start and slot.duration and slot.start + slot.duration < now()


def registration_deadline_is_passed(effect):
    """
    registration deadline has passed
    """
    return (
        effect.instance.registration_deadline
        and effect.instance.registration_deadline < date.today()
    )


def registration_deadline_is_not_passed(effect):
    """
    registration deadline hasn't passed
    """
    return not registration_deadline_is_passed(effect)


def deadline_is_passed(effect):
    """
    deadline has passed
    """
    return effect.instance.deadline and effect.instance.deadline < date.today()


def deadline_is_not_passed(effect):
    """
    deadline hasn't passed
    """
    return not deadline_is_passed(effect)


def start_is_not_passed(effect):
    """
    start date hasn't passed
    """
    return effect.instance.start is None or effect.instance.start > date.today()


def no_review_needed(effect):
    """
    no review needed
    """
    return not effect.instance.review


def is_open(effect):
    """
    is open
    """
    return effect.instance.status == "open"


def is_locked(effect):
    """
    is locked
    """
    return effect.instance.status == "full"


class TimeBasedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + []


@register(DateActivity)
class DateActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + []


class RegistrationActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + []


@register(DeadlineActivity)
class DeadlineActivityTriggers(RegistrationActivityTriggers):
    triggers = RegistrationActivityTriggers.triggers + []


class ScheduleActivityTriggers(RegistrationActivityTriggers):
    triggers = RegistrationActivityTriggers.triggers + [
        ModelChangedTrigger(
            "capacity",
            effects=[
                TransitionEffect(
                    ScheduleActivityStateMachine.fill,
                    conditions=[is_not_full, registration_deadline_is_not_passed],
                ),
                TransitionEffect(
                    ScheduleActivityStateMachine.unfill,
                    conditions=[is_full],
                ),
            ],
        ),
        ModelChangedTrigger(
            "registration_deadline",
            effects=[
                TransitionEffect(
                    ScheduleActivityStateMachine.unlock,
                    conditions=[registration_deadline_is_not_passed],
                ),
                TransitionEffect(
                    ScheduleActivityStateMachine.lock,
                    conditions=[registration_deadline_is_passed],
                ),
            ],
        ),
        ModelChangedTrigger(
            "deadline",
            effects=[
                TransitionEffect(
                    ScheduleActivityStateMachine.succeed,
                    conditions=[deadline_is_passed, has_participants],
                ),
                TransitionEffect(
                    ScheduleActivityStateMachine.expire,
                    conditions=[deadline_is_passed, has_no_participants],
                ),
                TransitionEffect(
                    ScheduleActivityStateMachine.reschedule,
                    conditions=[deadline_is_not_passed],
                ),
            ],
        ),
        ModelChangedTrigger(
            "status",
            effects=[
                TransitionEffect(
                    ScheduleActivityStateMachine.fill,
                    conditions=[is_full],
                ),
                TransitionEffect(
                    ScheduleActivityStateMachine.lock,
                    conditions=[registration_deadline_is_passed],
                ),
                TransitionEffect(
                    ScheduleActivityStateMachine.succeed,
                    conditions=[deadline_is_passed, has_participants],
                ),
                TransitionEffect(
                    ScheduleActivityStateMachine.expire,
                    conditions=[deadline_is_passed, has_no_participants],
                ),
                RelatedTransitionEffect(
                    "participants", ScheduleParticipantStateMachine("cancel")
                ),
                RelatedTransitionEffect(
                    "participants", ScheduleParticipantStateMachine("reset")
                ),
            ],
        ),
    ]


@register(PeriodicActivity)
class PeriodicActivityTriggers(RegistrationActivityTriggers):
    triggers = RegistrationActivityTriggers.triggers + []
