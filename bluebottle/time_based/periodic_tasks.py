from datetime import date
from django.db.models import DateTimeField, ExpressionWrapper, F

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.time_based.models import OnADateActivity, WithADeadlineActivity, OngoingActivity
from bluebottle.time_based.states import TimeBasedStateMachine
from bluebottle.time_based.triggers import has_applications, has_no_applications
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
            has_applications
        ]),
        TransitionEffect(TimeBasedStateMachine.cancel, conditions=[
            has_no_applications
        ]),
    ]

    def __str__(self):
        return _("Start an start when start date has passed.")


class OngoingActivityFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            deadline__lt=date.today(),
            status__in=['running', 'open', 'full']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.succeed, conditions=[
            has_applications
        ]),
        TransitionEffect(TimeBasedStateMachine.cancel, conditions=[
            has_no_applications
        ]),
    ]

    def __str__(self):
        return _("Finish an activity when deadline has passed.")


class OnADateActivityStartedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=timezone.now(),
            status__in=['open', 'full']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.start, conditions=[
            has_applications
        ]),
        TransitionEffect(TimeBasedStateMachine.cancel, conditions=[
            has_no_applications
        ]),
    ]

    def __str__(self):
        return _("Start an start when start date has passed.")


class OnADateActivityFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lt=ExpressionWrapper(timezone.now() - F('duration'), output_field=DateTimeField()),
            status__in=['running', 'open', 'full']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.succeed, conditions=[
            has_applications
        ]),
        TransitionEffect(TimeBasedStateMachine.cancel, conditions=[
            has_no_applications
        ]),
    ]

    def __str__(self):
        return _("Finish an activity when end time has passed.")


OnADateActivity.periodic_tasks = [OnADateActivityFinishedTask, OnADateActivityStartedTask]
WithADeadlineActivity.periodic_tasks = [TimeBasedActivityStartedTask, OngoingActivityFinishedTask]
OngoingActivity.periodic_tasks = [TimeBasedActivityStartedTask]
