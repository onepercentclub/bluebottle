from datetime import date
from django.utils.timezone import now

from bluebottle.fsm.triggers import register, ModelChangedTrigger, TransitionTrigger
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.notifications.effects import NotificationEffect

from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers, ContributorTriggers, ContributionTriggers
)

from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution
)
from bluebottle.time_based.messages import (
    DateChanged, DeadlineChanged,
    ActivitySucceededNotification, ActivitySucceededManuallyNotification,
    ActivityExpiredNotification, ActivityRejectedNotification,
    ActivityCancelledNotification,
    ParticipantAddedNotification, ParticipantCreatedNotification,
    ParticipantAcceptedNotification, ParticipantRejectedNotification,
    NewParticipantNotification
)
from bluebottle.time_based.effects import (
    CreateDateParticipationEffect, CreatePeriodParticipationEffect, SetEndDateEffect
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, DateStateMachine, PeriodStateMachine,
    ParticipantStateMachine, TimeContributionStateMachine
)


def is_full(effect):
    """
    the activity is full
    """
    return (
        effect.instance.capacity and
        effect.instance.capacity <= len(effect.instance.accepted_participants)
    )


def is_not_full(effect):
    """
    the activity is not full
    """
    return (
        effect.instance.capacity and
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
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start + effect.instance.duration < now()
    )


def is_not_finished(effect):
    """
    is not finished
    """
    return (
        effect.instance.start and
        effect.instance.duration and
        effect.instance.start + effect.instance.duration > now()
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
    egistration deadline hasn't passed
    """
    return (
        effect.instance.registration_deadline and
        effect.instance.registration_deadline > date.today()
    )


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
    return (
        effect.instance.deadline and
        effect.instance.deadline > date.today()
    )


def start_is_not_passed(effect):
    """
    start date hasn't passed
    """
    return (
        effect.instance.start and
        effect.instance.start > date.today()
    )


def is_started(effect):
    """
    has started
    """
    to_compare = now()

    if not isinstance(effect.instance, DateActivity):
        to_compare = to_compare.date()

    return (
        effect.instance.start and
        effect.instance.start < to_compare
    )


def is_not_started(effect):
    """
    hasn't started yet
    """
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

        TransitionTrigger(
            TimeBasedStateMachine.succeed,
            effects=[
                NotificationEffect(ActivitySucceededNotification),
                RelatedTransitionEffect(
                    'active_durations',
                    TimeContributionStateMachine.succeed
                )
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.reject,
            effects=[
                NotificationEffect(ActivityRejectedNotification),
            ]
        ),
        TransitionTrigger(
            TimeBasedStateMachine.cancel,
            effects=[
                NotificationEffect(ActivityCancelledNotification),
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                RelatedTransitionEffect(
                    'active_durations',
                    TimeContributionStateMachine.fail
                )
            ]
        ),
        TransitionTrigger(
            TimeBasedStateMachine.expire,
            effects=[
                NotificationEffect(ActivityExpiredNotification),
            ]
        ),
    ]


@register(DateActivity)
class DateTriggers(TimeBasedTriggers):
    triggers = TimeBasedTriggers.triggers + [

        TransitionTrigger(
            DateStateMachine.reschedule,
            effects=[
                RelatedTransitionEffect(
                    'active_durations',
                    TimeContributionStateMachine.reset
                ),

                TransitionEffect(TimeBasedStateMachine.lock, conditions=[is_full]),
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


@register(PeriodActivity)
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
            PeriodStateMachine.succeed_manually,
            effects=[
                SetEndDateEffect,
                RelatedTransitionEffect(
                    'active_durations',
                    TimeContributionStateMachine.succeed
                ),
                NotificationEffect(ActivitySucceededManuallyNotification),
            ]
        ),

        ModelChangedTrigger(
            'start',
            effects=[
                NotificationEffect(
                    DeadlineChanged,
                    conditions=[
                        start_is_not_passed
                    ]
                ),
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
    """
    automatically accept participants
    """
    return not effect.instance.activity.review


def needs_review(effect):
    """
    needs review
    """
    return effect.instance.activity.review


def is_not_user(effect):
    """
    User is not the participant
    """
    if 'user' in effect.options:
        return effect.instance.user != effect.options['user']
    return True


def is_user(effect):
    """
    User is the participant
    """
    if 'user' in effect.options:
        return effect.instance.user == effect.options['user']
    return False


def activity_will_be_full(effect):
    """
    the activity is full
    """
    activity = effect.instance.activity
    return (
        activity.capacity and
        activity.capacity == len(activity.accepted_participants) + 1
    )


def activity_will_not_be_full(effect):
    """
    the activity is full
    """
    activity = effect.instance.activity
    return (
        activity.capacity and
        activity.capacity >= len(activity.accepted_participants)
    )


def activity_is_finished(effect):
    """
    the activity has finished
    """
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


class ParticipantTriggers(ContributorTriggers):
    triggers = ContributorTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                NotificationEffect(
                    ParticipantCreatedNotification,
                    conditions=[
                        needs_review,
                        is_user
                    ]
                ),
                TransitionEffect(
                    ParticipantStateMachine.add,
                    conditions=[is_not_user]
                ),
                TransitionEffect(
                    ParticipantStateMachine.accept,
                    conditions=[
                        automatically_accept,
                        is_user
                    ]
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
                    'contributions',
                    TimeContributionStateMachine.reset,
                )
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.add,
            effects=[
                NotificationEffect(
                    ParticipantAddedNotification
                ),
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
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),

                RelatedTransitionEffect(
                    'finished_contributions',
                    TimeContributionStateMachine.succeed,
                ),
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.accept,
            effects=[
                NotificationEffect(
                    NewParticipantNotification,
                    conditions=[automatically_accept]
                ),
                NotificationEffect(
                    ParticipantAcceptedNotification,
                    conditions=[needs_review]
                ),
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
                    'contributions',
                    TimeContributionStateMachine.reset,
                ),

                RelatedTransitionEffect(
                    'finished_contributions',
                    TimeContributionStateMachine.succeed,
                ),
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.reject,
            effects=[
                NotificationEffect(
                    ParticipantRejectedNotification
                ),
                RelatedTransitionEffect(
                    'activity',
                    TimeBasedStateMachine.reopen,
                    conditions=[activity_will_not_be_full]
                ),

                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
                )
            ]
        ),

        TransitionTrigger(
            ParticipantStateMachine.mark_absent,
            effects=[
                RelatedTransitionEffect(
                    'contributions',
                    TimeContributionStateMachine.fail,
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
                    'contributions',
                    TimeContributionStateMachine.fail,
                )
            ]
        ),
    ]


@register(DateParticipant)
class OnADateParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreateDateParticipationEffect,
            ]
        ),
    ]


@register(PeriodParticipant)
class PeriodParticipantTriggers(ParticipantTriggers):
    triggers = ParticipantTriggers.triggers + [
        TransitionTrigger(
            ParticipantStateMachine.initiate,
            effects=[
                CreatePeriodParticipationEffect,
            ]
        ),

    ]


def duration_is_finished(effect):
    """
    contribution (session) has finished
    """
    return effect.instance.end is None or effect.instance.end < now()


@register(TimeContribution)
class TimeContributionTriggers(ContributionTriggers):
    triggers = ContributionTriggers.triggers + [
        TransitionTrigger(
            TimeContributionStateMachine.reset,
            effects=[
                TransitionEffect(TimeContributionStateMachine.succeed, conditions=[duration_is_finished]),
            ]
        ),

        TransitionTrigger(
            TimeContributionStateMachine.initiate,
            effects=[
                TransitionEffect(TimeContributionStateMachine.succeed, conditions=[duration_is_finished]),
            ]
        ),
    ]
