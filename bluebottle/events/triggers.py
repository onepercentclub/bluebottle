from datetime import timedelta
from django.utils import timezone

from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.fsm.triggers import ModelChangedTrigger, ModelDeletedTrigger

from bluebottle.events.models import Event, Participant
from bluebottle.events.messages import EventDateChanged
from bluebottle.events.states import EventStateMachine, ParticipantStateMachine


class CapacityChanged(ModelChangedTrigger):
    field = 'capacity'

    effects = [
        TransitionEffect('unfill', conditions=[EventStateMachine.is_not_full]),
        TransitionEffect('fill', conditions=[EventStateMachine.is_full]),
    ]


class DateChanged(ModelChangedTrigger):
    field = 'start'

    effects = [
        NotificationEffect(EventDateChanged),
        TransitionEffect('succeed', conditions=[EventStateMachine.should_finish, EventStateMachine.has_participants]),
        TransitionEffect('close', conditions=[EventStateMachine.should_finish, EventStateMachine.has_no_participants]),
        TransitionEffect('reopen', conditions=[EventStateMachine.should_open]),
        TransitionEffect('fill', conditions=[EventStateMachine.is_full]),
    ]


class Started(ModelChangedTrigger):
    @property
    def is_valid(self):
        "The event has started"
        return (
            self.instance.duration and
            (self.instance.start and self.instance.start < timezone.now()) and
            self.instance.status not in ('succeeded', 'closed', )
        )

    effects = [
        TransitionEffect('start', conditions=[EventStateMachine.should_start, EventStateMachine.has_participants]),
    ]


class Finished(ModelChangedTrigger):
    @property
    def is_valid(self):
        "The event has ended"
        return (
            self.instance.duration and
            (
                self.instance.start and
                self.instance.start + timedelta(hours=self.instance.duration) < timezone.now()
            ) and
            self.instance.status not in ('succeeded', 'closed', )
        )

    effects = [
        TransitionEffect('succeed', conditions=[EventStateMachine.should_finish, EventStateMachine.has_participants]),
        TransitionEffect('close', conditions=[EventStateMachine.should_finish, EventStateMachine.has_no_participants]),
    ]


Event.triggers = [CapacityChanged, DateChanged, Started, Finished]


class ParticipantDeleted(ModelDeletedTrigger):
    field = 'start'

    effects = [
        RelatedTransitionEffect(
            'activity',
            'close',
            conditions=[
                ParticipantStateMachine.event_is_finished,
                ParticipantStateMachine.event_will_be_empty
            ]
        ),
        RelatedTransitionEffect(
            'activity',
            'unfill',
            conditions=[
                ParticipantStateMachine.event_will_become_open,
                ParticipantStateMachine.event_is_not_finished
            ],
        ),
    ]


Participant.triggers = [ParticipantDeleted]
