from bluebottle.fsm.state import register, Transition, AllStates

from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwaveBankAccount
from django.utils.translation import gettext_lazy as _


@register(FlutterwavePayment)
class FlutterwavePaymentStateMachine(BasePaymentStateMachine):
    request_refund = None
    refund_requested = None


@register(FlutterwaveBankAccount)
class FlutterwaveBankAccountStateMachine(BankAccountStateMachine):

    migrate_to_lipisha = Transition(
        AllStates(),
        BankAccountStateMachine.rejected,
        name=_("Migrate to Lipisha"),
        description=_("Migrate to Lipisha account"),
        automatic=False
    )
