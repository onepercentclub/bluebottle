from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_telesom.models import TelesomPayment, TelesomBankAccount
from bluebottle.fsm.state import register


@register(TelesomPayment)
class TelesomPaymentStateMachine(BasePaymentStateMachine):
    request_refund = None
    refund_requested = None


@register(TelesomBankAccount)
class TelesomBankAccountStateMachine(BankAccountStateMachine):
    pass
