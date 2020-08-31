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
        TransitionEffect('reopen', conditions=[
            EventStateMachine.should_open,
            EventStateMachine.is_not_full
        ]),
        TransitionEffect('lock', conditions=[
            EventStateMachine.should_open,
            EventStateMachine.is_full
        ]),
    ]


class DateChangedTrigger(ModelChangedTrigger):
    field = 'start'

    effects = [
        NotificationEffect(EventDateChanged),
        TransitionEffect('succeed', conditions=[
            EventStateMachine.should_finish,
            EventStateMachine.has_participants
        ]),
        TransitionEffect('start', conditions=[
            EventStateMachine.should_start,
            EventStateMachine.has_participants
        ]),
        TransitionEffect('expire', conditions=[
            EventStateMachine.should_start,
            EventStateMachine.has_no_participants
        ]),
        TransitionEffect('expire', conditions=[
            EventStateMachine.should_finish,
            EventStateMachine.has_no_participants
        ]),
        TransitionEffect('reschedule', conditions=[
            EventStateMachine.should_open
        ]),
        TransitionEffect('lock', conditions=[
            EventStateMachine.is_full
        ]),
    ]


Event.triggers = [CapacityChangedTrigger, DateChangedTrigger]


class ParticipantDeletedTrigger(ModelDeletedTrigger):
    title = _('delete this participant')
    field = 'start'

    effects = [
        RelatedTransitionEffect(
            'activity',
            'cancel',
            conditions=[
                ParticipantStateMachine.event_is_finished,
                ParticipantStateMachine.event_will_be_empty
            ]
        ),
        RelatedTransitionEffect(
            'activity',
            'reopen',
            conditions=[
                ParticipantStateMachine.event_will_become_open,
                ParticipantStateMachine.event_is_not_finished
            ],
        ),
    ]

    def __unicode__(self):
        return unicode(_("Participant has been deleted"))


Participant.triggers = [ParticipantDeletedTrigger]
