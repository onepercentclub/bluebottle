from datetime import date
from django.db.models import DateTimeField, ExpressionWrapper, F

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.time_based.models import (
    DateActivity, PeriodActivity, PeriodParticipant, Duration
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, DurationStateMachine
)
from bluebottle.time_based.triggers import has_participants, has_no_participants
from bluebottle.time_based.effects import CreatePeriodParticipationEffect
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask


class TimeBasedActivityStartedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=date.today(),
            status__in=['open', 'full']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.start, conditions=[
            has_participants
        ]),
        TransitionEffect(TimeBasedStateMachine.cancel, conditions=[
            has_no_participants
        ]),
    ]

    def __str__(self):
        return _("Start an start when start date has passed.")


class PeriodActivityFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            deadline__lt=date.today(),
            status__in=['running', 'open', 'full']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.succeed, conditions=[
            has_participants
        ]),
        TransitionEffect(TimeBasedStateMachine.cancel, conditions=[
            has_no_participants
        ]),
    ]

    def __str__(self):
        return _("Finish an activity when deadline has passed.")


class NewPeriodForParticipantTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            current_period__lte=date.today(),
            activity__status='running',
            status__in=('accepted', 'new', )
        )

    effects = [
        CreatePeriodParticipationEffect
    ]

    def __str__(self):
        return _("Create a new period for participant")


class DateActivityStartedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=timezone.now(),
            status__in=['open', 'full']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.start, conditions=[
            has_participants
        ]),
        TransitionEffect(TimeBasedStateMachine.cancel, conditions=[
            has_no_participants
        ]),
    ]

    def __str__(self):
        return _("Start an start when start date has passed.")


class DateActivityFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lt=ExpressionWrapper(timezone.now() - F('duration'), output_field=DateTimeField()),
            status__in=['running', 'open', 'full']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.succeed, conditions=[
            has_participants
        ]),
        TransitionEffect(TimeBasedStateMachine.cancel, conditions=[
            has_no_participants
        ]),
    ]

    def __str__(self):
        return _("Finish an activity when end time has passed.")


class DurationFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            end__lt=timezone.now(),
            status='new',
            contributor__status='accepted'
        )

    effects = [
        TransitionEffect(DurationStateMachine.succeed),
    ]

    def __str__(self):
        return _("Finish an activity when end time has passed.")


DateActivity.periodic_tasks = [DateActivityFinishedTask, DateActivityStartedTask]
PeriodActivity.periodic_tasks = [
    TimeBasedActivityStartedTask, PeriodActivityFinishedTask
]
PeriodParticipant.periodic_tasks = [NewPeriodForParticipantTask]
Duration.periodic_tasks = [DurationFinishedTask]
