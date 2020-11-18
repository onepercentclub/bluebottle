from bluebottle.fsm.state import register

from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwaveBankAccount


@register(FlutterwavePayment)
class FlutterwavePaymentStateMachine(BasePaymentStateMachine):
    request_refund = None
    refund_requested = None


@register(FlutterwaveBankAccount)
class FlutterwaveBankAccountStateMachine(BankAccountStateMachine):
    pass
