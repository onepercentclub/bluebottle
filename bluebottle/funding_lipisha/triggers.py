from bluebottle.fsm.triggers import (
    TransitionTrigger, register
)
from bluebottle.funding.triggers import BankAccountTriggers
from bluebottle.funding_lipisha.effects import GenerateLipishaAccountsEffect
from bluebottle.funding_lipisha.models import LipishaBankAccount
from bluebottle.funding_lipisha.states import LipishaBankAccountStateMachine


@register(LipishaBankAccount)
class LipishaBankAccountTriggers(BankAccountTriggers):
    triggers = BankAccountTriggers.triggers + [
        TransitionTrigger(
            LipishaBankAccountStateMachine.verify,
            effects=[
                GenerateLipishaAccountsEffect
            ]
        ),
    ]
