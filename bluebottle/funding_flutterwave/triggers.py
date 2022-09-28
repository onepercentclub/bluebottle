from bluebottle.fsm.triggers import (
    TransitionTrigger, register
)
from bluebottle.funding.triggers import BankAccountTriggers
from bluebottle.funding_flutterwave.effects import MigrateToLipishaEffect
from bluebottle.funding_flutterwave.models import FlutterwaveBankAccount
from bluebottle.funding_flutterwave.states import FlutterwaveBankAccountStateMachine


@register(FlutterwaveBankAccount)
class FlutterwaveBankAccountTriggers(BankAccountTriggers):
    triggers = BankAccountTriggers.triggers + [
        TransitionTrigger(
            FlutterwaveBankAccountStateMachine.migrate_to_lipisha,
            effects=[
                MigrateToLipishaEffect
            ]
        ),
    ]
