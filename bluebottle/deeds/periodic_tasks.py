from datetime import date, timedelta

from django.utils.timezone import now

from bluebottle.deeds.messages import DeedReminderNotification
from bluebottle.notifications.effects import NotificationEffect
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.deeds.models import (
    Deed
)
from bluebottle.deeds.states import (
    DeedStateMachine
)
from bluebottle.deeds.triggers import has_participants, has_no_participants


class DeedStartedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=date.today(),
            status__in=['open']
        )

    effects = [
        TransitionEffect(DeedStateMachine.start)
    ]

    def __str__(self):
        return str(_("Start the activity when the start date has passed"))


class DeedFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            end__lte=date.today(),
            status__in=['running', 'open']
        )

    effects = [
        TransitionEffect(DeedStateMachine.succeed, conditions=[has_participants]),
        TransitionEffect(DeedStateMachine.expire, conditions=[has_no_participants])
    ]

    def __str__(self):
        return str(_("Finish the activity when the start date has passed"))


class DeedReminderTask(ModelPeriodicTask):

    def get_queryset(self):
        return Deed.objects.filter(
            start__lte=now() + timedelta(hours=24),
            status__in=['open', 'full']
        )

    effects = [
        NotificationEffect(
            DeedReminderNotification
        ),
    ]

    def __str__(self):
        return str(_("Send a reminder a day before the activity."))


Deed.periodic_tasks = [
    DeedStartedTask, DeedFinishedTask, DeedReminderTask
]
