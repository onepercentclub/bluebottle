from bluebottle.events.effects import SendEventEffect
from bluebottle.events.models import Event
from bluebottle.events.states import EventStateMachine
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import register, TriggerManager, TransitionTrigger


@register(Event)
class EventTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            EventStateMachine.initiate,
            effects=[
                TransitionEffect(
                    EventStateMachine.draft,
                )
            ]
        ),
        TransitionTrigger(
            EventStateMachine.draft,
            effects=[
                TransitionEffect(
                    EventStateMachine.publish,
                )
            ]
        ),
        TransitionTrigger(
            EventStateMachine.publish,
            effects=[
                SendEventEffect
                # Create wall update
                # Trigger webhook
            ]
        ),
    ]
