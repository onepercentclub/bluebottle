from datetime import timedelta

from django.utils import timezone

from bluebottle.activities.effects import Complete
from bluebottle.assignments.messages import AssignmentDateChanged
from bluebottle.assignments.models import Assignment, Applicant
from bluebottle.assignments.states import AssignmentStateMachine, ApplicantStateMachine
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger
from bluebottle.notifications.effects import NotificationEffect


class DateChanged(ModelChangedTrigger):
    field = 'start'

    effects = [
        NotificationEffect(AssignmentDateChanged),
        TransitionEffect(
            'succeed',
            conditions=[AssignmentStateMachine.should_finish, AssignmentStateMachine.has_accepted_applicants]),
        TransitionEffect(
            'close',
            conditions=[AssignmentStateMachine.should_finish, AssignmentStateMachine.has_no_accepted_applicants]),
        TransitionEffect('reopen', conditions=[AssignmentStateMachine.should_open]),
        TransitionEffect('fill', conditions=[AssignmentStateMachine.is_full]),
    ]


class CapacityChanged(ModelChangedTrigger):
    field = 'capacity'

    effects = [
        TransitionEffect('unfill', conditions=[AssignmentStateMachine.is_not_full]),
        TransitionEffect('fill', conditions=[AssignmentStateMachine.is_full]),
    ]


class Started(ModelChangedTrigger):
    @property
    def is_valid(self):
        "The event has started"
        return (
            self.instance.duration and
            (self.instance.date and self.instance.date < timezone.now()) and
            self.instance.status not in ('succeeded', 'closed', )
        )

    effects = [
        TransitionEffect(
            'start',
            conditions=[
                AssignmentStateMachine.should_start,
                AssignmentStateMachine.has_accepted_applicants
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


Assignment.triggers = [Complete, CapacityChanged, DateChanged, Started, Finished]


class TimeSpentChanged(ModelChangedTrigger):
    field = 'time_spent'

    effects = [
        TransitionEffect('succeed', conditions=[ApplicantStateMachine.has_time_spent]),
        TransitionEffect('fail', conditions=[ApplicantStateMachine.has_no_time_spent]),
    ]


Applicant.triggers = [TimeSpentChanged]
