from django.utils import timezone

from bluebottle.activities.triggers import ActivityTriggers, ContributorTriggers

from bluebottle.assignments.effects import SetTimeSpent, ClearTimeSpent
from bluebottle.assignments.messages import (
    AssignmentExpiredMessage, AssignmentApplicationMessage,
    ApplicantAcceptedMessage, ApplicantRejectedMessage, AssignmentCompletedMessage,
    AssignmentRejectedMessage, AssignmentCancelledMessage,
    AssignmentDateChanged, AssignmentDeadlineChanged
)
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.states import AssignmentStateMachine, ApplicantStateMachine
from bluebottle.follow.effects import UnFollowActivityEffect, FollowActivityEffect

from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    ModelChangedTrigger, ModelDeletedTrigger, TransitionTrigger, register
)

from bluebottle.notifications.effects import NotificationEffect


def initiative_is_approved(effect):
    return effect.instance.initiative.status == 'approved'


def in_the_future(effect):
    """is in the future"""
    return effect.instance.date > timezone.now()


def should_finish(effect):
    """end date has passed"""
    return effect.instance.end and effect.instance.end < timezone.now()


def should_start(effect):
    """start date has passed"""
    return effect.instance.start and effect.instance.start < timezone.now() and not should_finish(effect)


def has_deadline(effect):
    """has a deadline"""
    return effect.instance.end_date_type == 'deadline'


def is_on_date(effect):
    """takes place on a set date"""
    return effect.instance.end_date_type == 'on_date'


def should_open(effect):
    """registration deadline is in the future"""
    return effect.instance.start and effect.instance.start >= timezone.now() and not should_finish(effect)


def has_accepted_applicants(effect):
    """there are accepted applicants"""
    return len(effect.instance.accepted_applicants) > 0


def has_no_accepted_applicants(effect):
    """there are no accepted applicants"""
    return len(effect.instance.accepted_applicants) == 0


def has_new_or_accepted_applicants(effect):
    """there are accepted applicants"""
    return len(effect.instance.accepted_applicants) > 0 or len(effect.instance.new_applicants) > 0


def has_no_new_or_accepted_applicants(effect):
    """there are no accepted applicants"""
    return len(effect.instance.accepted_applicants) == 0 and len(effect.instance.new_applicants) == 0


def is_not_full(effect):
    """the task is not full"""
    return effect.instance.capacity > len(effect.instance.accepted_applicants)


def is_full(effect):
    """the task is full"""
    return effect.instance.capacity <= len(effect.instance.accepted_applicants)


@register(Assignment)
class AssignmentTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        TransitionTrigger(
            AssignmentStateMachine.submit,
            effects=[
                TransitionEffect(
                    AssignmentStateMachine.auto_approve,
                    conditions=[
                        initiative_is_approved,
                        should_open
                    ]
                ),
                TransitionEffect(
                    AssignmentStateMachine.expire,
                    conditions=[should_finish, has_no_accepted_applicants]
                ),
                TransitionEffect(
                    AssignmentStateMachine.succeed,
                    conditions=[should_finish, has_accepted_applicants]
                ),
            ]

        ),

        TransitionTrigger(
            AssignmentStateMachine.start,
            effects=[
                RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.activate),
            ]
        ),

        TransitionTrigger(
            AssignmentStateMachine.auto_approve,
            effects=[
                RelatedTransitionEffect('applicants', ApplicantStateMachine.reset),
                TransitionEffect(
                    AssignmentStateMachine.expire,
                    conditions=[should_finish, has_no_accepted_applicants]
                ),
            ]
        ),

        TransitionTrigger(
            AssignmentStateMachine.reject,
            effects=[
                NotificationEffect(AssignmentRejectedMessage),
            ]
        ),

        TransitionTrigger(
            AssignmentStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.fail),
                NotificationEffect(AssignmentCancelledMessage),
            ]
        ),

        TransitionTrigger(
            AssignmentStateMachine.expire,
            effects=[
                NotificationEffect(AssignmentExpiredMessage),
            ]
        ),

        TransitionTrigger(
            AssignmentStateMachine.reschedule,
            effects=[
                RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.reaccept),
            ]
        ),

        TransitionTrigger(
            AssignmentStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.succeed),
                RelatedTransitionEffect('new_applicants', ApplicantStateMachine.succeed),
                NotificationEffect(AssignmentCompletedMessage)
            ]
        ),

        TransitionTrigger(
            AssignmentStateMachine.restore,
            effects=[
                RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.reset)
            ]
        ),

        ModelChangedTrigger(
            'date',
            effects=[
                NotificationEffect(
                    AssignmentDeadlineChanged,
                    conditions=[
                        in_the_future,
                        has_deadline
                    ]
                ),
                NotificationEffect(
                    AssignmentDateChanged,
                    conditions=[
                        in_the_future,
                        is_on_date
                    ]
                ),
                TransitionEffect(
                    AssignmentStateMachine.succeed,
                    conditions=[
                        should_finish,
                        has_new_or_accepted_applicants
                    ]
                ),
                TransitionEffect(
                    AssignmentStateMachine.expire,
                    conditions=[
                        should_finish,
                        has_no_new_or_accepted_applicants
                    ]
                ),
                TransitionEffect(
                    AssignmentStateMachine.reschedule,
                    conditions=[
                        should_open
                    ]
                ),
                TransitionEffect(
                    AssignmentStateMachine.lock,
                    conditions=[
                        is_full
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'registration_deadline',
            effects=[
                TransitionEffect(
                    AssignmentStateMachine.reschedule,
                    conditions=[
                        should_open
                    ]
                ),
                TransitionEffect(
                    AssignmentStateMachine.start,
                    conditions=[
                        should_start,
                        has_accepted_applicants
                    ]
                ),
                TransitionEffect(
                    AssignmentStateMachine.expire,
                    conditions=[
                        should_start,
                        has_no_accepted_applicants
                    ]
                ),
            ]
        ),
        ModelChangedTrigger(
            'capacity',

            effects=[
                TransitionEffect(AssignmentStateMachine.reopen, conditions=[is_not_full]),
                TransitionEffect(AssignmentStateMachine.lock, conditions=[is_full]),
            ]
        )

    ]


def has_time_spent(effect):
    """time spent is set"""
    return effect.instance.time_spent


def has_no_time_spent(effect):
    """time spent is not set"""
    return not effect.instance.time_spent


def assignment_will_become_full(effect):
    """task will be full"""
    activity = effect.instance.activity

    return activity.capacity == len(activity.accepted_applicants) + 1


def assignment_will_become_open(effect):
    """task will not be full"""
    activity = effect.instance.activity
    return activity.capacity == len(activity.accepted_applicants)


def assignment_is_finished(effect):
    """task is finished"""
    return effect.instance.activity.end < timezone.now()


def assignment_is_not_finished(effect):
    "task is not finished"
    return not effect.instance.activity.date < timezone.now()


def assignment_will_be_empty(effect):
    """task be empty"""
    return len(effect.instance.activity.accepted_applicants) == 1


@register(Applicant)
class ApplicantTriggers(ContributorTriggers):
    triggers = [
        TransitionTrigger(
            ApplicantStateMachine.initiate,
            effects=[
                NotificationEffect(AssignmentApplicationMessage),
                FollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ApplicantStateMachine.accept,
            effects=[
                TransitionEffect(ApplicantStateMachine.succeed, conditions=[assignment_is_finished]),
                RelatedTransitionEffect(
                    'activity',
                    AssignmentStateMachine.lock,
                    conditions=[assignment_will_become_full]
                ),
                RelatedTransitionEffect(
                    'activity',
                    AssignmentStateMachine.succeed,
                    conditions=[assignment_is_finished]
                ),
                NotificationEffect(ApplicantAcceptedMessage)
            ]
        ),

        TransitionTrigger(
            ApplicantStateMachine.reaccept,
            effects=[
                RelatedTransitionEffect(
                    'activity',
                    AssignmentStateMachine.lock,
                    conditions=[assignment_will_become_full]
                ),
                ClearTimeSpent,
            ]
        ),

        TransitionTrigger(
            ApplicantStateMachine.reject,
            effects=[
                RelatedTransitionEffect('activity', AssignmentStateMachine.reopen),
                NotificationEffect(ApplicantRejectedMessage),
                UnFollowActivityEffect
            ]
        ),


        TransitionTrigger(
            ApplicantStateMachine.withdraw,
            effects=[
                UnFollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ApplicantStateMachine.reapply,
            effects=[
                FollowActivityEffect,
                NotificationEffect(AssignmentApplicationMessage)
            ]
        ),

        TransitionTrigger(
            ApplicantStateMachine.succeed,
            effects=[
                SetTimeSpent
            ]
        ),

        TransitionTrigger(
            ApplicantStateMachine.mark_absent,
            effects=[
                ClearTimeSpent,
                RelatedTransitionEffect(
                    'activity', AssignmentStateMachine.cancel,
                    conditions=[assignment_is_finished, assignment_will_be_empty]
                ),
                UnFollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ApplicantStateMachine.mark_present,
            effects=[
                SetTimeSpent,
                RelatedTransitionEffect(
                    'activity', AssignmentStateMachine.succeed,
                    conditions=[assignment_is_finished]
                ),
                FollowActivityEffect
            ]
        ),

        TransitionTrigger(
            ApplicantStateMachine.reset,
            effects=[
                ClearTimeSpent,
            ]
        ),

        ModelChangedTrigger(
            'time_spent',
            effects=[
                TransitionEffect(ApplicantStateMachine.mark_present, conditions=[has_time_spent]),
                TransitionEffect(ApplicantStateMachine.mark_absent, conditions=[has_no_time_spent]),
            ]
        ),

        ModelDeletedTrigger(
            effects=[

                RelatedTransitionEffect(
                    'activity',
                    AssignmentStateMachine.cancel,
                    conditions=[
                        assignment_is_finished,
                        assignment_will_be_empty
                    ]
                ),
                RelatedTransitionEffect(
                    'activity',
                    AssignmentStateMachine.reopen,
                    conditions=[
                        assignment_will_become_open,
                        assignment_is_not_finished
                    ],
                ),
            ]
        )
    ]
