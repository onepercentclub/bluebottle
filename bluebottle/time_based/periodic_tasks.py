from datetime import date, timedelta

from django.db.models import DateTimeField, ExpressionWrapper, F
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import CreatePeriodTimeContributionEffect
from bluebottle.time_based.messages import ReminderSingleDateNotification
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity, PeriodParticipant, TimeContribution, DateActivitySlot
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, TimeContributionStateMachine, ActivitySlotStateMachine
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


class NewPeriodForParticipantTask(ModelPeriodicTask):
    """
    Create a new contribution when, the participant is new or
    accepted, and the activity is open or full.
    """

    def get_queryset(self):
        return self.model.objects.filter(
            current_period__lte=date.today(),
            status__in=('accepted', 'new',)
        ).filter(
            Q(
                activity__status__in=['open', 'full'],
            )
        )

    effects = [
        CreatePeriodTimeContributionEffect
    ]

    def __str__(self):
        return str(_("Create a new contribution for participant"))


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


class DateActivityReminderTask(ModelPeriodicTask):

    def get_queryset(self):
        return DateActivity.objects.filter(slots__start__lte=timezone.now() + timedelta(days=5),
                                           status__in=['open', 'full']
                                           )

    def has_one_slot(effect):
        return effect.instance.slots.count() == 1

    effects = [
        NotificationEffect(
            ReminderSingleDateNotification,
            conditions=[
                has_one_slot
            ]
        ),
    ]

    def __str__(self):
        return str(_("Send a reminder five days before the activity."))


DateActivity.periodic_tasks = [
    TimeBasedActivityRegistrationDeadlinePassedTask,
    DateActivityReminderTask
]

DateActivitySlot.periodic_tasks = [
    SlotStartedTask,
    SlotFinishedTask,
]

PeriodActivity.periodic_tasks = [
    PeriodActivityFinishedTask,
    TimeBasedActivityRegistrationDeadlinePassedTask
]

PeriodParticipant.periodic_tasks = [NewPeriodForParticipantTask]
TimeContribution.periodic_tasks = [TimeContributionFinishedTask]
