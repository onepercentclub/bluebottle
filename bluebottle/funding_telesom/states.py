from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_telesom.models import TelesomPayment, TelesomBankAccount


class TelesomPaymentStateMachine(BasePaymentStateMachine):
    model = TelesomPayment

    request_refund = None
    refund_requested = None


class TelesomBankAccountStateMachine(BankAccountStateMachine):
    model = TelesomBankAccount
