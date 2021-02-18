from builtins import str
from datetime import timedelta

from django.db.models.expressions import F
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.assignments.messages import AssignmentReminderDeadline, AssignmentReminderOnDate
from bluebottle.assignments.models import Assignment
from bluebottle.assignments.states import AssignmentStateMachine
from bluebottle.assignments.triggers import (
    has_accepted_applicants, has_no_accepted_applicants,
    has_new_or_accepted_applicants, has_no_new_or_accepted_applicants,
    is_on_date, has_deadline
)
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.notifications.effects import NotificationEffect


class AssignmentStartOnDateTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            date__lte=timezone.now(),
            end_date_type='on_date',
            status__in=[
                AssignmentStateMachine.full,
                AssignmentStateMachine.open
            ]
        )

    effects = [
        TransitionEffect(AssignmentStateMachine.start, conditions=[
            has_accepted_applicants
        ]),
        TransitionEffect(AssignmentStateMachine.expire, conditions=[
            has_no_accepted_applicants
        ]),
    ]

    def __str__(self):
        return str(_("Start a task on a set date."))


class AssignmentStartDeadlineTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            registration_deadline__lte=timezone.now(),
            end_date_type='deadline',
            status__in=[
                AssignmentStateMachine.full,
                AssignmentStateMachine.open
            ]
        )

    effects = [
        TransitionEffect(AssignmentStateMachine.start, conditions=[
            has_new_or_accepted_applicants
        ]),
        TransitionEffect(AssignmentStateMachine.expire, conditions=[
            has_no_new_or_accepted_applicants
        ]),
    ]

    def __str__(self):
        return str(_("Start a task with deadline after registration deadline has passed."))


class AssignmentFinishedDeadlineTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            date__lt=timezone.now(),
            end_date_type='deadline',
            status__in=[
                AssignmentStateMachine.running,
                AssignmentStateMachine.full,
                AssignmentStateMachine.open
            ]
        )

    effects = [
        TransitionEffect(AssignmentStateMachine.succeed, conditions=[
            has_new_or_accepted_applicants
        ]),
        TransitionEffect(AssignmentStateMachine.expire, conditions=[
            has_no_new_or_accepted_applicants
        ]),
    ]

    def __str__(self):
        return str(_("Finish a task when deadline has passed."))


class AssignmentFinishedOnDateTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            date__lte=timezone.now() - timedelta(hours=1) * F('duration'),
            end_date_type='on_date',
            status__in=[
                AssignmentStateMachine.running,
                AssignmentStateMachine.full,
                AssignmentStateMachine.open
            ]
        )

    effects = [
        TransitionEffect(AssignmentStateMachine.succeed, conditions=[
            has_new_or_accepted_applicants
        ]),
        TransitionEffect(AssignmentStateMachine.expire, conditions=[
            has_no_new_or_accepted_applicants
        ]),
    ]

    def __str__(self):
        return str(_("Finish a task after it has ended (date + duration)."))


class AssignmentRegistrationOnDateTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            registration_deadline__lt=timezone.now(),
            end_date_type='on_date',
            status__in=[
                AssignmentStateMachine.full,
                AssignmentStateMachine.open
            ]
        )

    effects = [
        TransitionEffect(AssignmentStateMachine.lock, conditions=[
            has_new_or_accepted_applicants
        ]),
        TransitionEffect(AssignmentStateMachine.expire, conditions=[
            has_no_new_or_accepted_applicants
        ]),
    ]

    def __str__(self):
        return str(_("Make sure users can't sign up after registration date has passed on a task with a set date."))


class AssignmentRegistrationReminderTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            date__lte=timezone.now() + timedelta(days=5),
            status__in=[
                AssignmentStateMachine.full,
                AssignmentStateMachine.open
            ]
        )

    effects = [
        NotificationEffect(
            AssignmentReminderDeadline,
            conditions=[
                has_deadline
            ]
        ),
        NotificationEffect(
            AssignmentReminderOnDate,
            conditions=[
                is_on_date
            ]
        )]

    def __str__(self):
        return str(_("Send a reminder if the task deadline/date is in 5 days."))


Assignment.periodic_tasks = [
    AssignmentStartOnDateTask,
    AssignmentStartDeadlineTask,
    AssignmentFinishedOnDateTask,
    AssignmentFinishedDeadlineTask,
    AssignmentRegistrationOnDateTask,
    AssignmentRegistrationReminderTask
]
