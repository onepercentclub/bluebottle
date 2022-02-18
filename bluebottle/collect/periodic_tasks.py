from datetime import date, timedelta

from django.utils.translation import gettext_lazy as _

from bluebottle.collect.messages import CollectActivityReminderNotification
from bluebottle.collect.models import (
    CollectActivity
)
from bluebottle.collect.states import (
    CollectActivityStateMachine, CollectContributorStateMachine
)
from bluebottle.collect.triggers import has_contributors, has_no_contributors, has_no_end_date
from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.notifications.effects import NotificationEffect


class CollectActivityStartedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=date.today(),
            status__in=['open']
        )

    effects = [
        RelatedTransitionEffect(
            'contributors',
            CollectContributorStateMachine.succeed,
            conditions=[has_no_end_date]
        ),
    ]

    def __str__(self):
        return str(_("Start the activity when the start date has passed"))


class CollectActivityFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            end__lte=date.today(),
            status__in=['running', 'open']
        )

    effects = [
        TransitionEffect(CollectActivityStateMachine.succeed, conditions=[has_contributors]),
        TransitionEffect(CollectActivityStateMachine.expire, conditions=[has_no_contributors])
    ]

    def __str__(self):
        return str(_("Finish the activity when the start date has passed"))


class CollectActivityReminderTask(ModelPeriodicTask):

    def get_queryset(self):
        return CollectActivity.objects.filter(
            start__lte=date.today() + timedelta(hours=24),
            status__in=['open', 'full']
        )

    effects = [
        NotificationEffect(
            CollectActivityReminderNotification
        ),
    ]

    def __str__(self):
        return str(_("Send a reminder a day before the activity."))


CollectActivity.periodic_tasks = [
    CollectActivityStartedTask, CollectActivityFinishedTask, CollectActivityReminderTask
]
