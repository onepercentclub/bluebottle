from datetime import timedelta

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.assignments.messages import AssignmentDateChanged
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.states import AssignmentStateMachine, ApplicantStateMachine
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger, ModelDeletedTrigger
from bluebottle.notifications.effects import NotificationEffect


class DateChanged(ModelChangedTrigger):
    field = 'date'

    effects = [
        NotificationEffect(AssignmentDateChanged),
        TransitionEffect(
            'succeed',
            conditions=[AssignmentStateMachine.should_finish, AssignmentStateMachine.has_accepted_applicants]),
        TransitionEffect(
            'expire',
            conditions=[AssignmentStateMachine.should_finish, AssignmentStateMachine.has_no_accepted_applicants]),
        TransitionEffect('reopen', conditions=[AssignmentStateMachine.should_open]),
        TransitionEffect('lock', conditions=[AssignmentStateMachine.is_full]),
    ]


class CapacityChanged(ModelChangedTrigger):
    field = 'capacity'

    effects = [
        TransitionEffect('reopen', conditions=[AssignmentStateMachine.is_not_full]),
        TransitionEffect('lock', conditions=[AssignmentStateMachine.is_full]),
    ]


class Started(ModelChangedTrigger):
    @property
    def is_valid(self):
        "The event has started"
        return (
            self.instance.duration and (
                self.instance.date and (
                    self.instance.date < timezone.now() and
                    self.instance.date + timedelta(hours=self.instance.duration) > timezone.now()
                )
            ) and
            self.instance.status not in ('succeeded', 'closed', )
        )

    effects = [
        TransitionEffect(
            'start',
            conditions=[
                AssignmentStateMachine.should_start,
                AssignmentStateMachine.has_accepted_applicants
            ]),
        TransitionEffect(
            'expire',
            conditions=[
                AssignmentStateMachine.should_start,
                AssignmentStateMachine.has_no_accepted_applicants
            ]),
    ]


class Finished(ModelChangedTrigger):
    @property
    def is_valid(self):
        "The event has ended"
        return (
            self.instance.duration and
            (
                self.instance.date and
                self.instance.date + timedelta(hours=self.instance.duration) < timezone.now()
            ) and
            self.instance.status not in ('succeeded', 'closed', )
        )

    effects = [
        TransitionEffect(
            'succeed',
            conditions=[
                AssignmentStateMachine.should_finish,
                AssignmentStateMachine.has_accepted_applicants
            ]),
        TransitionEffect(
            'close',
            conditions=[
                AssignmentStateMachine.should_finish,
                AssignmentStateMachine.has_no_accepted_applicants
            ]),
    ]


Assignment.triggers = [CapacityChanged, DateChanged, Started, Finished]


class TimeSpentChanged(ModelChangedTrigger):
    field = 'time_spent'

    effects = [
        TransitionEffect('mark_present', conditions=[ApplicantStateMachine.has_time_spent]),
        TransitionEffect('mark_absent', conditions=[ApplicantStateMachine.has_no_time_spent]),
    ]


class ApplicantDeleted(ModelDeletedTrigger):
    title = _('delete this participant')
    effects = [
        RelatedTransitionEffect(
            'activity',
            'close',
            conditions=[
                ApplicantStateMachine.assignment_is_finished,
                ApplicantStateMachine.assignment_will_be_empty
            ]
        ),
        RelatedTransitionEffect(
            'activity',
            'reopen',
            conditions=[
                ApplicantStateMachine.assignment_will_become_open,
                ApplicantStateMachine.assignment_is_not_finished
            ],
        ),
    ]


Applicant.triggers = [TimeSpentChanged, ApplicantDeleted]
