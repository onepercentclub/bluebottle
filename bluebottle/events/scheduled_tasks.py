from django.utils.timezone import now

from bluebottle.events.models import Event
from bluebottle.events.states import EventStateMachine
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.scheduled_tasks import ModelScheduledTask


class FinishedScheduledTask(ModelScheduledTask):

    def get_queryset(self):
        return self.model.objects.filter(
            end__lte=now(),
            status__in=['running', 'open']
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


Event.scheduled_tasks = [FinishedScheduledTask]
