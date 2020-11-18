from datetime import date
from django.utils.timezone import now

from bluebottle.fsm.triggers import register, ModelChangedTrigger, TransitionTrigger
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.notifications.effects import NotificationEffect

from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers, ContributionValueTriggers
)

from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, Duration
)
from bluebottle.time_based.effects import (
    CreateDateParticipationEffect, CreatePeriodParticipationEffect
)
from bluebottle.time_based.messages import DateChanged, DeadlineChanged
from bluebottle.time_based.states import (
    TimeBasedStateMachine, DateStateMachine, PeriodStateMachine,
    ParticipantStateMachine, PeriodParticipantStateMachine, DurationStateMachine
)


def is_full(effect):
    "the activity is full"
    return (
        effect.instance.capacity and
        effect.instance.capacity <= len(effect.instance.accepted_applications)
    )


def is_not_full(effect):
    "the activity is not full"
    return (
        effect.instance.capacity and
        effect.instance.capacity > len(effect.instance.accepted_applications)
    )


def has_participants(effect):
    return len(effect.instance.active_participants) > 0


def has_no_participants(effect):
    return len(effect.instance.active_participants) == 0


def is_finished(effect):
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start + effect.instance.duration
    )


def is_not_finished(effect):
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start + effect.instance.duration > now()
    )


def registration_deadline_is_passed(effect):
    return (
        effect.instance.registration_deadline and
        effect.instance.registration_deadline < date.today()
    )


def registration_deadline_is_not_passed(effect):
    return (
        effect.instance.registration_deadline and
        effect.instance.registration_deadline > date.today()
    )


def deadline_is_passed(effect):

    return (
        effect.instance.deadline and
        effect.instance.deadline < date.today()
    )


def deadline_is_not_passed(effect):
    return (
        effect.instance.deadline and
        effect.instance.deadline > date.today()
    )


def is_started(effect):
    to_compare = now()

    if not isinstance(effect.instance, DateActivity):
        to_compare = to_compare.date()

    return (
        effect.instance.start and
        effect.instance.start < to_compare
    )


def is_not_started(effect):
    to_compare = now()

    if not isinstance(effect.instance, DateActivity):
        to_compare = to_compare.date()

    return (
        effect.instance.start and
        effect.instance.start > to_compare
    )


class TimeBasedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        ModelChangedTrigger(
            'capacity',
            effects=[
                TransitionEffect(TimeBasedStateMachine.reopen, conditions=[
                    is_not_full
                ]),
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[
                    is_full
                ]),
            ]
        ),

        ModelChangedTrigger(
            'registration_deadline',
            effects=[
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[
                    registration_deadline_is_passed
                ]),
                TransitionEffect(TimeBasedStateMachine.reopen, conditions=[
                    registration_deadline_is_not_passed
                ]),
            ]
        ),
    ]


@register(DateActivity)
class DateTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [
        TransitionTrigger(
            DateStateMachine.reschedule,
            effects=[
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[is_full]),
            ]
        ),

        TransitionTrigger(
            DateStateMachine.succeed,
            effects=[
                RelatedTransitionEffect(
                    'accepted_durations',
                    DurationStateMachine.succeed
                )
            ]
        ),

        TransitionTrigger(
            DateStateMachine.reschedule,
            effects=[
                RelatedTransitionEffect(
                    'accepted_durations',
                    DurationStateMachine.reset
                )
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                NotificationEffect(
                    DateChanged,
                    conditions=[
                        is_not_finished
                    ]
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
                TransitionEffect(
                    DateStateMachine.reschedule,
                    conditions=[
                        is_not_finished
                    ]
                ),
            ]
        )
    ]


@ register(PeriodActivity)
class PeriodTriggers(TimeBasedTriggers):

    triggers = TimeBasedTriggers.triggers + [
        TransitionTrigger(
            PeriodStateMachine.reschedule,
            effects=[
                TransitionEffect(TimeBasedStateMachine.lock, conditions=[is_full]),
                TransitionEffect(
                    TimeBasedStateMachine.lock, conditions=[registration_deadline_is_passed]
                )
            ]
        ),

        TransitionTrigger(
            PeriodStateMachine.cancel,
            effects=[
                RelatedTransitionEffect(
                    'durations', DurationStateMachine.fail
                )
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                TransitionEffect(
                    DateStateMachine.start,
                    conditions=[is_started]
                ),

                TransitionEffect(
                    DateStateMachine.reopen,
                    conditions=[is_not_started, is_not_full]
                ),

                TransitionEffect(
                    DateStateMachine.lock,
                    conditions=[is_not_started, is_full]
                ),

                TransitionEffect(
                    TimeBasedStateMachine.lock,
                    conditions=[is_not_started, registration_deadline_is_passed]
                )
            ]
        ),
        ModelChangedTrigger(
            'deadline',
            effects=[
                NotificationEffect(
                    DeadlineChanged,
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


def automatically_accept(effect):
    return not effect.instance.activity.review


def activity_will_be_full(effect):
    "the activity is full"
    activity = effect.instance.activity
    return (
        activity.capacity and
        activity.capacity == len(activity.accepted_applications) + 1
    )


def activity_will_not_be_full(effect):
    "the activity is full"
    activity = effect.instance.activity
    return (
        activity.capacity and
        activity.capacity >= len(activity.accepted_applications)
    )


def activity_is_finished(effect):
    activity = effect.instance.activity

    if isinstance(activity, DateActivity):
        return (
            activity.start and
            activity.duration and
            activity.start + activity.duration < now()
        )
    elif isinstance(activity, PeriodActivity):
        return (
            activity.deadline and
            activity.deadline < date.today()
        )
    else:
        return False


class ApplicationTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[automatically_accept]
                ),

            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reapply,
            effects=[
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[automatically_accept]
                ),

                RelatedTransitionEffect(
                    'contribution_values',
                    DurationStateMachine.reset,
                )
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.lock,
                    conditions=[activity_will_be_full]
                ),

                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.succeed,
                    conditions=[activity_is_finished]
                ),

                RelatedTransitionEffect(
                    'contribution_values',
                    DurationStateMachine.reset,
                ),

                RelatedTransitionEffect(
                    'finished_durations',
                    DurationStateMachine.succeed,
                ),
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reject,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                    conditions=[activity_will_not_be_full]
                ),

                RelatedTransitionEffect(
                    'contribution_values',
                    DurationStateMachine.fail,
                )
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.withdraw,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                    conditions=[activity_will_not_be_full]
                ),

                RelatedTransitionEffect(
                    'contribution_values',
                    DurationStateMachine.fail,
                )
            ]
        ),
    ]


@register(DateParticipant)
class OnADateApplicationTriggers(ApplicationTriggers):
    triggers = ApplicationTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreateDateParticipationEffect,
            ]
        ),
    ]


@register(PeriodParticipant)
class PeriodApplicationTriggers(ApplicationTriggers):
    triggers = ApplicationTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreatePeriodParticipationEffect,
            ]
        ),

        TransitionTrigger(
            PeriodParticipantStateMachine.stop,
            effects=[
                RelatedTransitionEffect(
                    'current_duration',
                    DurationStateMachine.fail
                )
            ]
        ),
    ]


def duration_is_finished(effect):
    return effect.instance.end is None or effect.instance.end < now()


@ register(Duration)
class DurationTriggers(ContributionValueTriggers):
    triggers = ContributionValueTriggers.triggers + [
        TransitionTrigger(
            DurationStateMachine.reset,
            effects=[
                TransitionEffect(DurationStateMachine.succeed, conditions=[duration_is_finished]),
            ]
        ),
    ]
