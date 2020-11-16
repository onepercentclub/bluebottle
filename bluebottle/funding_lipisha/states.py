from bluebottle.fsm.state import register

from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaBankAccount


@register(LipishaPayment)
class LipishaPaymentStateMachine(BasePaymentStateMachine):
    request_refund = None
    refund_requested = None


@register(LipishaBankAccount)
class LipishaBankAccountStateMachine(BankAccountStateMachine):
    pass
