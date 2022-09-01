from bluebottle.activities.triggers import ActivityTriggers
from bluebottle.fsm.triggers import (
    TransitionTrigger, register
)
from bluebottle.funding_lipisha.effects import GenerateLipishaAccountsEffect
from bluebottle.funding_lipisha.models import LipishaBankAccount
from bluebottle.funding_lipisha.states import LipishaBankAccountStateMachine


@register(LipishaBankAccount)
class LipishaBankAccountTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [

        TransitionTrigger(
            LipishaBankAccountStateMachine.verify,
            effects=[
                GenerateLipishaAccountsEffect
            ]
        ),
    ]
