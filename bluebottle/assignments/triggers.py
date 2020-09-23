from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.effects import CreateOrganizer

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


def is_not_full(effect):
    """the task is not full"""
    return effect.instance.capacity > len(effect.instance.accepted_applicants)


def is_full(effect):
    """the task is full"""
    return effect.instance.capacity <= len(effect.instance.accepted_applicants)


@register(Assignment)
class InitiateTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.initiate

    effects = [CreateOrganizer]


@register(Assignment)
class SubmitAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.submit

    effects = [
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


@register(Assignment)
class StartAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.start

    effects = [
        RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.activate),
    ]


@register(Assignment)
class ApproveAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.auto_approve

    effects = [
        RelatedTransitionEffect('organizer', OrganizerStateMachine.succeed),
        RelatedTransitionEffect('applicants', ApplicantStateMachine.reset),
        TransitionEffect(
            AssignmentStateMachine.expire,
            conditions=[should_finish, has_no_accepted_applicants]
        ),
    ]


@register(Assignment)
class RejectAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.reject

    effects = [
        RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
        NotificationEffect(AssignmentRejectedMessage),
    ]


@register(Assignment)
class CancelAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.cancel

    effects = [
        RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
        RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.fail),
        NotificationEffect(AssignmentCancelledMessage),
    ]


@register(Assignment)
class ExpireAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.expire

    effects = [
        NotificationEffect(AssignmentExpiredMessage),
        RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
    ]


@register(Assignment)
class RescheduleAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.reschedule

    effects = [
        RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.reaccept),
    ]


@register(Assignment)
class SuceedAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.succeed

    effects = [
        RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.succeed),
        NotificationEffect(AssignmentCompletedMessage)
    ]


@register(Assignment)
class RestoreAssignmentTrigger(TransitionTrigger):
    transition = AssignmentStateMachine.restore
    effects = [
        RelatedTransitionEffect('organizer', OrganizerStateMachine.reset),
        RelatedTransitionEffect('accepted_applicants', ApplicantStateMachine.reset)

    ]


@register(Assignment)
class DateChangedTrigger(ModelChangedTrigger):
    field = 'date'

    effects = [
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
                has_accepted_applicants
            ]
        ),
        TransitionEffect(
            AssignmentStateMachine.expire,
            conditions=[
                should_finish,
                has_no_accepted_applicants
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


@register(Assignment)
class RegistrationDeadlineChangedTrigger(ModelChangedTrigger):
    field = 'registration_deadline'

    effects = [
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


@register(Assignment)
class CapacityChangedTrigger(ModelChangedTrigger):
    field = 'capacity'

    effects = [
        TransitionEffect(AssignmentStateMachine.reopen, conditions=[is_not_full]),
        TransitionEffect(AssignmentStateMachine.lock, conditions=[is_full]),
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
class InitiateApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.initiate

    effects = [
        NotificationEffect(AssignmentApplicationMessage),
        FollowActivityEffect
    ]


@register(Applicant)
class AcceptApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.accept

    effects = [
        TransitionEffect(ApplicantStateMachine.succeed, conditions=[assignment_is_finished]),
        RelatedTransitionEffect('activity', AssignmentStateMachine.lock, conditions=[assignment_will_become_full]),
        RelatedTransitionEffect(
            'activity',
            AssignmentStateMachine.succeed,
            conditions=[assignment_is_finished]
        ),
        NotificationEffect(ApplicantAcceptedMessage)
    ]


@register(Applicant)
class ReacceptApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.reaccept

    effects = [
        RelatedTransitionEffect('activity', AssignmentStateMachine.lock, conditions=[assignment_will_become_full]),
        ClearTimeSpent,
    ]


@register(Applicant)
class RejectApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.reject

    effects = [
        RelatedTransitionEffect('activity', AssignmentStateMachine.reopen),
        NotificationEffect(ApplicantRejectedMessage),
        UnFollowActivityEffect
    ]


@register(Applicant)
class WithdrawApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.withdraw

    effects = [
        UnFollowActivityEffect
    ]


@register(Applicant)
class ReapplyApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.reapply

    effects = [
        FollowActivityEffect,
        NotificationEffect(AssignmentApplicationMessage)
    ]


@register(Applicant)
class SucceedApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.succeed

    effects = [
        SetTimeSpent
    ]


@register(Applicant)
class MarkAbsentApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.mark_absent

    effects = [
        ClearTimeSpent,
        RelatedTransitionEffect(
            'activity', AssignmentStateMachine.cancel,
            conditions=[assignment_is_finished, assignment_will_be_empty]
        ),
        UnFollowActivityEffect
    ]


@register(Applicant)
class MarkPresentApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.mark_present

    effects = [
        SetTimeSpent,
        RelatedTransitionEffect(
            'activity', AssignmentStateMachine.succeed,
            conditions=[assignment_is_finished]
        ),
        FollowActivityEffect
    ]


@register(Applicant)
class ResetApplicantTransition(TransitionTrigger):
    transition = ApplicantStateMachine.reset

    effects = [ClearTimeSpent]


@register(Applicant)
class TimeSpentChangedTrigger(ModelChangedTrigger):
    field = 'time_spent'

    effects = [
        TransitionEffect(ApplicantStateMachine.mark_present, conditions=[has_time_spent]),
        TransitionEffect(ApplicantStateMachine.mark_absent, conditions=[has_no_time_spent]),
    ]


@register(Applicant)
class ApplicantDeletedTrigger(ModelDeletedTrigger):
    title = _('delete this participant')
    effects = [
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
