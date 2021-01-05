from bluebottle.fsm.state import register
from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayBankAccount


@register(VitepayPayment)
class VitepayPaymentStateMachine(BasePaymentStateMachine):
    request_refund = None
    refund_requested = None


@register(VitepayBankAccount)
class VitepayBankAccountStateMachine(BankAccountStateMachine):
    pass
