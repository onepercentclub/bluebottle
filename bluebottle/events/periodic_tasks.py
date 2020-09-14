from datetime import timedelta
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.events.messages import EventReminderMessage
from bluebottle.events.models import Event
from bluebottle.events.states import EventStateMachine
from bluebottle.events.triggers import (
    event_should_finish, event_has_participants, event_has_no_participants, event_should_start
)
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.periodic_tasks import ModelPeriodicTask
from bluebottle.notifications.effects import NotificationEffect


class EventFinishedTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            end__lte=timezone.now(),
            status__in=['running', 'open', 'full']
        )

    effects = [
        TransitionEffect(EventStateMachine.succeed, conditions=[
            event_should_finish,
            event_has_participants
        ]),
        TransitionEffect(EventStateMachine.succeed, conditions=[
            event_should_finish,
            event_has_no_participants
        ]),
    ]

    def __unicode__(self):
        return unicode(_("Finish an event when end time has passed."))


class EventStartTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=timezone.now(),
            status__in=['open', 'full']
        )

    effects = [
        TransitionEffect(EventStateMachine.succeed, conditions=[
            event_should_start,
            event_has_participants
        ]),
        TransitionEffect(EventStateMachine.succeed, conditions=[
            event_should_start,
            event_has_no_participants
        ]),
    ]

    def __unicode__(self):
        return unicode(_("Start an event when start time ha passed."))


class EventReminderTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=timezone.now() + timedelta(days=5),
            status__in=['open', 'full']
        )

    effects = [
        NotificationEffect(
            EventReminderMessage
        )

    ]

    def __unicode__(self):
        return unicode(_("Send a reminder five days before the event starts."))


Event.periodic_tasks = [EventFinishedTask, EventStartTask, EventReminderTask]
