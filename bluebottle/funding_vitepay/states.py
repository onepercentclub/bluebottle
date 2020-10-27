from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayBankAccount


class VitepayPaymentStateMachine(BasePaymentStateMachine):
    model = VitepayPayment

    request_refund = None
    refund_requested = None


class VitepayBankAccountStateMachine(BankAccountStateMachine):
    model = VitepayBankAccount
