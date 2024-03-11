from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger, TriggerManager
)
from bluebottle.time_based.effects.effects import CreateNextSlotEffect, CreatePeriodicParticipantsEffect
from bluebottle.time_based.models import PeriodicSlot
from bluebottle.time_based.states import (
    PeriodicSlotStateMachine
)
from bluebottle.time_based.states.participants import PeriodicParticipantStateMachine


@register(PeriodicSlot)
class PeriodicSlotTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            PeriodicSlotStateMachine.initiate,
            effects=[
                CreatePeriodicParticipantsEffect,
            ]
        ),
        TransitionTrigger(
            PeriodicSlotStateMachine.finish,
            effects=[
                CreateNextSlotEffect,
                RelatedTransitionEffect(
                    'participants',
                    PeriodicParticipantStateMachine.succeed,
                ),
            ]
        ),
    ]
