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
    CreateFirstSlotEffect
)
from bluebottle.time_based.effects.contributions import (
    RescheduleActivityDurationsEffect,
)
from bluebottle.time_based.models import (
    DateActivity,
    DateActivitySlot,
    DeadlineActivity,
    PeriodicActivity, ScheduleActivity,
)
from bluebottle.time_based.states import (
    DateStateMachine,
    ParticipantStateMachine,
    TimeBasedStateMachine,
    TimeContributionStateMachine,
)
from bluebottle.time_based.states.participants import (
    RegistrationParticipantStateMachine,
)
from bluebottle.time_based.states.states import (
    RegistrationActivityStateMachine,
    PeriodicActivityStateMachine,
)


def is_full(effect):
    """
    the activity is full
    """
    if getattr(effect.instance, 'team_activity', None) == 'teams':
        accepted_teams = effect.instance.teams.filter(status__in=['open', 'running', 'finished']).count()
        return (
            effect.instance.capacity and
            effect.instance.capacity <= accepted_teams
        )

    if isinstance(effect.instance, DateActivity) and effect.instance.slots.count() > 1:
        return False

    return (
        effect.instance.capacity and
        effect.instance.capacity <= len(effect.instance.accepted_participants)
    )


def is_not_full(effect):
    """
    the activity is not full
    """
    if getattr(effect.instance, 'team_activity', None) == 'teams':
        accepted_teams = effect.instance.teams.filter(status__in=['open', 'running', 'finished']).count()
        return (
            not effect.instance.capacity or
            effect.instance.capacity > accepted_teams
        )

    return (
        not effect.instance.capacity or
        effect.instance.capacity > len(effect.instance.accepted_participants)
    )


def has_participants(effect):
    """ has participants"""
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
        slot = effect.instance.slots.order_by('start').last()
    return (
        slot and
        slot.start and
        slot.duration and
        slot.start + slot.duration < now()
    )


def registration_deadline_is_passed(effect):
    """
    registration deadline has passed
    """
    return (
        effect.instance.registration_deadline and
        effect.instance.registration_deadline < date.today()
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
    return (
        effect.instance.deadline and
        effect.instance.deadline < date.today()
    )


def deadline_is_not_passed(effect):
    """
    deadline hasn't passed
    """
    return not deadline_is_passed(effect)


def start_is_not_passed(effect):
    """
    start date hasn't passed
    """
    return (
        effect.instance.start is None or
        effect.instance.start > date.today()
    )


def no_review_needed(effect):
    """
    no review needed
    """
    return not effect.instance.review


def is_open(effect):
    """
    is open
    """
    return effect.instance.status == 'open'


def is_locked(effect):
    """
    is locked
    """
    return effect.instance.status == 'full'


class TimeBasedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger(
            'registration_deadline',
            effects=[
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[
                        registration_deadline_is_passed,
                        is_open
                    ]
                ),
                TransitionEffect(
                    TimeBasedStateMachine.reopen,
                    conditions=[
                        registration_deadline_is_not_passed,
                        is_locked
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'capacity',
            effects=[
                TransitionEffect(
                    TimeBasedStateMachine.reopen,
                    conditions=[
                        is_not_full,
                        registration_deadline_is_not_passed
                    ]
                ),
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[
                        is_full,
                        registration_deadline_is_not_passed
                    ]
                ),
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.publish,
            effects=[
                RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed),
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.succeed,
            effects=[
                NotificationEffect(ActivitySucceededNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed),
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.reject,
            effects=[
                NotificationEffect(ActivityRejectedNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.cancel,
            effects=[
                NotificationEffect(ActivityCancelledNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail),
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.restore,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset),
                NotificationEffect(ActivityRestoredNotification)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.expire,
            effects=[
                NotificationEffect(ActivityExpiredNotification),
            ]
        ),
        ModelChangedTrigger(
            'review',
            effects=[
                RelatedTransitionEffect(
                    'pending_participants',
                    ParticipantStateMachine.accept,
                    conditions=[no_review_needed]
                ),
            ]
        ),
    ]


@register(DateActivity)
class DateActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [
        TransitionTrigger(
            DateStateMachine.reopen_manually,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),

        TransitionTrigger(
            DateStateMachine.auto_approve,
            effects=[
                TransitionEffect(
                    DateStateMachine.succeed,
                    conditions=[
                        is_finished, has_participants
                    ]
                ),
                TransitionEffect(
                    DateStateMachine.expire,
                    conditions=[
                        is_finished, has_no_participants
                    ]
                ),
            ]
        ),

        TransitionTrigger(
            DateStateMachine.auto_publish,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.succeed,
                    conditions=[has_organizer]
                ),
            ]
        ),

        TransitionTrigger(
            DateStateMachine.publish,
            effects=[
                RelatedTransitionEffect(
                    'organizer',
                    OrganizerStateMachine.succeed,
                    conditions=[has_organizer]
                ),

                TransitionEffect(
                    DateStateMachine.succeed,
                    conditions=[
                        is_finished, has_participants
                    ]
                ),
                TransitionEffect(
                    DateStateMachine.expire,
                    conditions=[
                        is_finished, has_no_participants
                    ]
                ),
                RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed),
            ]
        ),
    ]


class RegistrationActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [

        TransitionTrigger(
            RegistrationActivityStateMachine.reschedule,
            effects=[
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[
                        is_full,
                    ]
                ),
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[
                        registration_deadline_is_passed,
                    ]
                )
            ]
        ),

        TransitionTrigger(
            RegistrationActivityStateMachine.succeed,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed),
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'accepted_participants',
                    ParticipantStateMachine.cancel
                ),
            ],
        ),
        TransitionTrigger(
            TimeBasedStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    "accepted_participants", RegistrationParticipantStateMachine.reject
                ),
            ],
        ),
        TransitionTrigger(
            TimeBasedStateMachine.restore,
            effects=[
                RelatedTransitionEffect(
                    "participants", RegistrationParticipantStateMachine.restore
                ),
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                RescheduleActivityDurationsEffect,
                TransitionEffect(
                    RegistrationActivityStateMachine.reopen,
                    conditions=[
                        is_not_full, registration_deadline_is_not_passed
                    ]
                ),
                TransitionEffect(
                    RegistrationActivityStateMachine.lock,
                    conditions=[
                        is_full,
                    ]
                ),
                TransitionEffect(
                    RegistrationActivityStateMachine.lock,
                    conditions=[
                        registration_deadline_is_passed,
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'deadline',
            effects=[
                RescheduleActivityDurationsEffect,
                TransitionEffect(
                    RegistrationActivityStateMachine.succeed,
                    conditions=[
                        deadline_is_passed,
                        has_participants
                    ]
                ),
                TransitionEffect(
                    RegistrationActivityStateMachine.expire,
                    conditions=[
                        deadline_is_passed,
                        has_no_participants
                    ]
                ),
                TransitionEffect(
                    RegistrationActivityStateMachine.reopen,
                    conditions=[
                        deadline_is_not_passed
                    ]
                ),
            ]
        )
    ]


@register(DeadlineActivity)
class DeadlineActivityTriggers(RegistrationActivityTriggers):
    triggers = RegistrationActivityTriggers.triggers + [
        ModelChangedTrigger(
            "capacity",
            effects=[
                TransitionEffect(
                    TimeBasedStateMachine.reopen,
                    conditions=[is_not_full, registration_deadline_is_not_passed],
                ),
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[is_full, registration_deadline_is_not_passed],
                ),
            ],
        ),
    ]


@register(ScheduleActivity)
class ScheduleActivityTriggers(RegistrationActivityTriggers):
    triggers = RegistrationActivityTriggers.triggers + [
        ModelChangedTrigger(
            "capacity",
            effects=[
                TransitionEffect(
                    TimeBasedStateMachine.reopen,
                    conditions=[is_not_full, registration_deadline_is_not_passed],
                ),
                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[is_full, registration_deadline_is_not_passed],
                ),
            ],
        ),
    ]


@register(PeriodicActivity)
class PeriodicActivityTriggers(RegistrationActivityTriggers):
    triggers = RegistrationActivityTriggers.triggers + [
        TransitionTrigger(
            PeriodicActivityStateMachine.publish,
            effects=[
                CreateFirstSlotEffect,
            ]
        ),
        TransitionTrigger(
            PeriodicActivityStateMachine.auto_publish,
            effects=[
                CreateFirstSlotEffect,
            ]
        ),
    ]
