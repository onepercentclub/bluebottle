from datetime import timedelta
from django.db.models.expressions import F
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.assignments.messages import AssignmentReminderDeadline, AssignmentReminderOnDate
from bluebottle.assignments.models import Assignment
from bluebottle.assignments.states import AssignmentStateMachine
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
        TransitionEffect('start', conditions=[
            AssignmentStateMachine.has_accepted_applicants
        ]),
        TransitionEffect('expire', conditions=[
            AssignmentStateMachine.has_no_accepted_applicants
        ]),
    ]

    def __unicode__(self):
        return unicode(_("Start a task on a set date."))


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
        TransitionEffect('start', conditions=[
            AssignmentStateMachine.has_accepted_applicants
        ]),
        TransitionEffect('expire', conditions=[
            AssignmentStateMachine.has_no_accepted_applicants
        ]),
    ]

    def __unicode__(self):
        return unicode(_("Start a task with deadline after registration deadline has passed."))


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
        TransitionEffect('succeed', conditions=[
            AssignmentStateMachine.has_accepted_applicants
        ]),
        TransitionEffect('close', conditions=[
            AssignmentStateMachine.has_no_accepted_applicants
        ]),
    ]


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
        TransitionEffect('succeed', conditions=[
            AssignmentStateMachine.has_accepted_applicants
        ]),
        TransitionEffect('close', conditions=[
            AssignmentStateMachine.has_no_accepted_applicants
        ]),
    ]


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
        TransitionEffect('lock', conditions=[
            AssignmentStateMachine.has_accepted_applicants
        ]),
        TransitionEffect('expire', conditions=[
            AssignmentStateMachine.has_no_accepted_applicants
        ]),
    ]


class AssignmentRegistrationReminderTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            date__lte=timezone.now() + timedelta(days=5),
            status__in=[
                AssignmentStateMachine.full,
                AssignmentStateMachine.open
            ]
        )

    def is_on_date(assignment):
        return getattr(assignment, 'end_date_type') == 'on_date'

    def has_deadline(assignment):
        return getattr(assignment, 'end_date_type') == 'deadline'

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


Assignment.scheduled_tasks = [
    AssignmentStartOnDateTask,
    AssignmentStartDeadlineTask,
    AssignmentFinishedOnDateTask,
    AssignmentFinishedDeadlineTask,
    AssignmentRegistrationOnDateTask,
    AssignmentRegistrationReminderTask
]
