from datetime import date, timedelta

from django.db.models import DateTimeField, ExpressionWrapper, F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.messages import ReminderSlotNotification
from bluebottle.time_based.models import (
    DateActivity, DeadlineActivity, PeriodicActivity, PeriodicSlot, TimeContribution, DateActivitySlot
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, TimeContributionStateMachine, ActivitySlotStateMachine
)
from bluebottle.time_based.states.states import PeriodicSlotStateMachine
from bluebottle.time_based.triggers.triggers import has_participants, has_no_participants


class TimeBasedActivityRegistrationDeadlinePassedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            registration_deadline__lte=date.today(),
            status__in=['open']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.lock, conditions=[
            has_participants
        ]),
        TransitionEffect(TimeBasedStateMachine.expire, conditions=[
            has_no_participants
        ]),
    ]

    def __str__(self):
        return str(_("Lock an activity when the registration date has passed."))


class DateActivityFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            status__in=['open', 'full']
        ).exclude(
            slots__status__in=['open', 'full', 'running']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.succeed, conditions=[
            has_participants
        ]),
        TransitionEffect(TimeBasedStateMachine.expire, conditions=[
            has_no_participants
        ]),
    ]

    def __str__(self):
        return str(_("Finish an activity when all slots are completed."))


class SlotStartedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=timezone.now(),
            status__in=['open', 'full']
        )

    effects = [
        TransitionEffect(ActivitySlotStateMachine.start),
    ]

    def __str__(self):
        return str(_("Start the slot."))


class SlotFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lt=ExpressionWrapper(timezone.now() - F('duration'), output_field=DateTimeField()),
            status__in=['open', 'full', 'running']
        )

    effects = [
        TransitionEffect(ActivitySlotStateMachine.finish),
    ]

    def __str__(self):
        return str(_("Finish a slot when end time has passed."))


class TimeContributionFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            end__lt=timezone.now(),
            status='new',
            contributor__status__in=('accepted', 'stopped')
        )

    effects = [
        TransitionEffect(TimeContributionStateMachine.succeed),
    ]

    def __str__(self):
        return str(_("Finish an activity when end time has passed."))


class DateActivitySlotReminderTask(ModelPeriodicTask):

    def get_queryset(self):
        slots = DateActivitySlot.objects.filter(
            start__lte=timezone.now() + timedelta(hours=25),
            start__gt=timezone.now() + timedelta(hours=20),
            status__in=['open', 'full'],
            activity__status__in=['open', 'full']
        )
        return slots

    effects = [
        NotificationEffect(
            ReminderSlotNotification,
        ),
    ]

    def __str__(self):
        return str(_("Send a reminder 24 hours before the activity slot."))


class ActivityFinishedTask(ModelPeriodicTask):
    def get_queryset(self):
        return self.model.objects.filter(
            deadline__lt=date.today(),
            status__in=['open', 'full']
        )

    effects = [
        TransitionEffect(TimeBasedStateMachine.succeed, conditions=[
            has_participants
        ]),
        TransitionEffect(TimeBasedStateMachine.expire, conditions=[
            has_no_participants
        ]),
    ]

    def __str__(self):
        return str(_("Finish an activity when deadline has passed."))


class PeriodicSlotStartedTask(ModelPeriodicTask):
    def get_queryset(self):
        return PeriodicSlot.objects.filter(
            start__lte=timezone.now(),
            status="new"
        )

    effects = [
        TransitionEffect(PeriodicSlotStateMachine.start)
    ]

    def __str__(self):
        return str(_("Start a new slot when the current one is finished"))


class PeriodicSlotFinishedTask(ModelPeriodicTask):
    def get_queryset(self):
        return PeriodicSlot.objects.filter(
            end__lte=timezone.now(),
            status="running"
        )

    effects = [
        TransitionEffect(PeriodicSlotStateMachine.finish)
    ]

    def __str__(self):
        return str(_("Start a new slot when the current one is finished"))


DateActivity.periodic_tasks = [
    TimeBasedActivityRegistrationDeadlinePassedTask,
    DateActivityFinishedTask,
]

DateActivitySlot.periodic_tasks = [
    DateActivitySlotReminderTask,
    SlotStartedTask,
    SlotFinishedTask,
]

TimeContribution.periodic_tasks = [TimeContributionFinishedTask]

DeadlineActivity.periodic_tasks = [ActivityFinishedTask]
PeriodicActivity.periodic_tasks = [ActivityFinishedTask]
PeriodicSlot.periodic_tasks = [PeriodicSlotStartedTask, PeriodicSlotFinishedTask]
