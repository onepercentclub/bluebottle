from datetime import timedelta
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import TransitionEffect, RelatedTransitionEffect
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.fsm.triggers import ModelChangedTrigger, ModelDeletedTrigger

from bluebottle.events.models import Event, Participant
from bluebottle.events.messages import EventDateChanged
from bluebottle.events.states import EventStateMachine, ParticipantStateMachine


class CapacityChangedTrigger(ModelChangedTrigger):
    field = 'capacity'

    effects = [
        TransitionEffect('unfill', conditions=[EventStateMachine.is_not_full]),
        TransitionEffect('fill', conditions=[EventStateMachine.is_full]),
    ]


class DateChangedTrigger(ModelChangedTrigger):
    field = 'start'

    effects = [
        NotificationEffect(EventDateChanged),
        TransitionEffect('succeed', conditions=[EventStateMachine.should_finish, EventStateMachine.has_participants]),
        TransitionEffect('close', conditions=[EventStateMachine.should_finish, EventStateMachine.has_no_participants]),
        TransitionEffect('reopen', conditions=[EventStateMachine.should_open]),
        TransitionEffect('fill', conditions=[EventStateMachine.is_full]),
    ]


class StartedTrigger(ModelChangedTrigger):
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

    def __unicode__(self):
        return unicode(_("Start date has passed"))


class FinishedTrigger(ModelChangedTrigger):
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

    def __unicode__(self):
        return unicode(_("Event has changed"))


Event.triggers = [CapacityChangedTrigger, DateChangedTrigger, StartedTrigger, FinishedTrigger]


class ParticipantDeletedTrigger(ModelDeletedTrigger):
    title = _('delete this participant')
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

    def __unicode__(self):
        return unicode(_("Participant has been deleted"))


Participant.triggers = [ParticipantDeletedTrigger]
