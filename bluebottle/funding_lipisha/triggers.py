from bluebottle.fsm.triggers import (
    TransitionTrigger, register, TriggerManager
)
from bluebottle.funding_lipisha.effects import GenerateLipishaAccountsEffect
from bluebottle.funding_lipisha.models import LipishaBankAccount
from bluebottle.funding_lipisha.states import LipishaBankAccountStateMachine


@register(LipishaBankAccount)
class LipishaBankAccountTriggers(TriggerManager):
    triggers = [

        TransitionTrigger(
            LipishaBankAccountStateMachine.verify,
            effects=[
                GenerateLipishaAccountsEffect
            ]
        ),
    ]
