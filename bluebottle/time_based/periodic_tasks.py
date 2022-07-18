from datetime import date, timedelta

from django.db.models import DateTimeField, ExpressionWrapper, F
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.messages import ReminderSlotNotification
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity, TimeContribution, DateActivitySlot,
    PeriodActivitySlot
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, TimeContributionStateMachine, ActivitySlotStateMachine,
    PeriodActivitySlotStateMachine
)
from bluebottle.time_based.triggers import has_participants, has_no_participants


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


class PeriodActivityFinishedTask(ModelPeriodicTask):

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
        return DateActivitySlot.objects.filter(
            start__lte=timezone.now() + timedelta(days=5),
            start__gt=timezone.now(),
            status__in=['open', 'full'],
            activity__status__in=['open', 'full']
        )

    effects = [
        NotificationEffect(
            ReminderSlotNotification,
        ),
    ]

    def __str__(self):
        return str(_("Send a reminder five days before the activity slot."))


def period_activity_slot_has_participants(effect):
    return effect.instance.slot_participants.filter(participant__status='accepted')


def period_activity_slot_has_no_participants(effect):
    return not period_activity_slot_has_participants(effect)


class PeriodActivitySlotFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return PeriodActivitySlot.objects.filter(
            end__lt=timezone.now().date(),
            status='running',
            activity__status__in=['open', 'full']
        )

    effects = [
        TransitionEffect(PeriodActivitySlotStateMachine.finish, conditions=[
            period_activity_slot_has_participants
        ]),
        TransitionEffect(PeriodActivitySlotStateMachine.expire, conditions=[
            period_activity_slot_has_no_participants
        ]),
    ]

    def __str__(self):
        return str(_("Finish the period activity slot when it ended"))


class PeriodActivitySlotStartedTask(ModelPeriodicTask):

    def get_queryset(self):
        return PeriodActivitySlot.objects.filter(
            start__lte=timezone.now().date(),
            status='draft',
            activity__status__in=['open', 'full']
        )

    effects = [
        TransitionEffect(PeriodActivitySlotStateMachine.start),
    ]

    def __str__(self):
        return str(_("Start the period activity slot when it starts"))


DateActivity.periodic_tasks = [
    TimeBasedActivityRegistrationDeadlinePassedTask,
]

DateActivitySlot.periodic_tasks = [
    DateActivitySlotReminderTask,
    SlotStartedTask,
    SlotFinishedTask,
]

PeriodActivity.periodic_tasks = [
    PeriodActivityFinishedTask,
    TimeBasedActivityRegistrationDeadlinePassedTask
]

TimeContribution.periodic_tasks = [TimeContributionFinishedTask]
PeriodActivitySlot.periodic_tasks = [PeriodActivitySlotFinishedTask, PeriodActivitySlotStartedTask]
