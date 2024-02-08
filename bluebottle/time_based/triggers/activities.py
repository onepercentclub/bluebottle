from datetime import date

from django.utils.timezone import now

from bluebottle.activities.messages import (
    ActivitySucceededNotification,
    ActivityExpiredNotification, ActivityRejectedNotification,
    ActivityCancelledNotification, ActivityRestoredNotification
)
from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers, has_organizer
)
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    register, ModelChangedTrigger, TransitionTrigger
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import (
    SetEndDateEffect,
    ClearDeadlineEffect,
    ActiveTimeContributionsTransitionEffect, UnsetCapacityEffect, RescheduleOverallPeriodActivityDurationsEffect, )
from bluebottle.time_based.effects.contributions import RescheduleDeadlineActivityDurationsEffect
from bluebottle.time_based.messages import (
    DeadlineChangedNotification,
    ActivitySucceededManuallyNotification
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateActivitySlot, DeadlineActivity
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, DateStateMachine, PeriodStateMachine, ParticipantStateMachine, TimeContributionStateMachine,
    DeadlineActivityStateMachine
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

    if (
        isinstance(effect.instance, DateActivity) and
        effect.instance.slots.count() > 1 and
        effect.instance.slot_selection == 'free'
    ):
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
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail)
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

        ModelChangedTrigger(
            'slot_selection',
            effects=[
                UnsetCapacityEffect
            ]
        ),

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


@register(PeriodActivity)
class PeriodActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [

        ModelChangedTrigger(
            ['start', 'deadline'],
            effects=[
                RescheduleOverallPeriodActivityDurationsEffect
            ]
        ),

        TransitionTrigger(
            PeriodStateMachine.reschedule,
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
            DateStateMachine.reopen_manually,
            effects=[
                ClearDeadlineEffect,
            ]
        ),

        TransitionTrigger(
            PeriodStateMachine.succeed_manually,
            effects=[
                SetEndDateEffect,
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed),
                NotificationEffect(ActivitySucceededManuallyNotification),
            ]
        ),

        TransitionTrigger(
            PeriodStateMachine.succeed,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed),
                SetEndDateEffect,
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                NotificationEffect(
                    DeadlineChangedNotification,
                    conditions=[start_is_not_passed]
                ),
                TransitionEffect(
                    PeriodStateMachine.reopen,
                    conditions=[
                        is_not_full, registration_deadline_is_not_passed
                    ]
                ),
                TransitionEffect(
                    PeriodStateMachine.lock,
                    conditions=[
                        is_full,
                    ]
                ),
                TransitionEffect(
                    PeriodStateMachine.lock,
                    conditions=[
                        registration_deadline_is_passed,
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'deadline',
            effects=[
                NotificationEffect(
                    DeadlineChangedNotification,
                    conditions=[
                        deadline_is_not_passed
                    ]
                ),
                TransitionEffect(
                    DateStateMachine.succeed,
                    conditions=[
                        deadline_is_passed, has_participants
                    ]
                ),
                TransitionEffect(
                    DateStateMachine.expire,
                    conditions=[
                        deadline_is_passed, has_no_participants
                    ]
                ),
                TransitionEffect(
                    PeriodStateMachine.reschedule,
                    conditions=[
                        deadline_is_not_passed
                    ]
                ),
            ]
        )
    ]


@register(DeadlineActivity)
class DeadlineActivityTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [

        TransitionTrigger(
            PeriodStateMachine.reschedule,
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
            PeriodStateMachine.succeed,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed),
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                RescheduleDeadlineActivityDurationsEffect,
                NotificationEffect(
                    DeadlineChangedNotification,
                    conditions=[start_is_not_passed]
                ),
                TransitionEffect(
                    PeriodStateMachine.reopen,
                    conditions=[
                        is_not_full, registration_deadline_is_not_passed
                    ]
                ),
                TransitionEffect(
                    PeriodStateMachine.lock,
                    conditions=[
                        is_full,
                    ]
                ),
                TransitionEffect(
                    PeriodStateMachine.lock,
                    conditions=[
                        registration_deadline_is_passed,
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'deadline',
            effects=[
                RescheduleDeadlineActivityDurationsEffect,
                NotificationEffect(
                    DeadlineChangedNotification,
                    conditions=[
                        deadline_is_not_passed
                    ]
                ),
                TransitionEffect(
                    DeadlineActivityStateMachine.succeed,
                    conditions=[
                        deadline_is_passed,
                        has_participants
                    ]
                ),
                TransitionEffect(
                    DeadlineActivityStateMachine.expire,
                    conditions=[
                        deadline_is_passed,
                        has_no_participants
                    ]
                ),
                TransitionEffect(
                    DeadlineActivityStateMachine.reopen,
                    conditions=[
                        deadline_is_not_passed
                    ]
                ),
            ]
        )
    ]
