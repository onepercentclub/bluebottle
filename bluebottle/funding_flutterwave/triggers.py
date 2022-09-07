from bluebottle.fsm.triggers import (
    TransitionTrigger, register, TriggerManager
)
from bluebottle.funding_flutterwave.effects import MigrateToLipishaEffect
from bluebottle.funding_flutterwave.models import FlutterwaveBankAccount
from bluebottle.funding_flutterwave.states import FlutterwaveBankAccountStateMachine


@register(FlutterwaveBankAccount)
class FlutterwaveBankAccountTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            FlutterwaveBankAccountStateMachine.migrate_to_lipisha,
            effects=[
                MigrateToLipishaEffect
            ]
        ),
    ]
