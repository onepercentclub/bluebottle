from bluebottle.events.effects import (
    EventWebhookEffect,
    SendEventEffect,
    CreateActivityUpdateEffect,
    CreateContributionUpdateEffect
)
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
                    EventStateMachine.publish,
                )
            ]
        ),
        TransitionTrigger(
            EventStateMachine.publish,
            effects=[
                SendEventEffect,
                CreateActivityUpdateEffect,
                CreateContributionUpdateEffect,
                EventWebhookEffect
            ]
        ),
    ]
