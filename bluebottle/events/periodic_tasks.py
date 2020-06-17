from datetime import timedelta
from django.utils import timezone

from bluebottle.events.messages import EventReminderMessage
from bluebottle.events.models import Event
from bluebottle.events.states import EventStateMachine
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
        TransitionEffect('succeed', conditions=[
            EventStateMachine.should_finish,
            EventStateMachine.has_participants
        ]),
        TransitionEffect('close', conditions=[
            EventStateMachine.should_finish,
            EventStateMachine.has_no_participants
        ]),
    ]


class EventStartTask(ModelPeriodicTask):

    def get_queryset(self):
        return self.model.objects.filter(
            start__lte=timezone.now(),
            status__in=['open', 'full']
        )

    effects = [
        TransitionEffect('start', conditions=[
            EventStateMachine.should_start,
            EventStateMachine.has_participants
        ]),
        TransitionEffect('expire', conditions=[
            EventStateMachine.should_start,
            EventStateMachine.has_no_participants
        ]),
    ]


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


Event.scheduled_tasks = [EventFinishedTask, EventStartTask, EventReminderTask]
