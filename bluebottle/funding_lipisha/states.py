from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaBankAccount


class LipishaPaymentStateMachine(BasePaymentStateMachine):
    model = LipishaPayment

    request_refund = None
    refund_requested = None


class LipishaBankAccountStateMachine(BankAccountStateMachine):
    model = LipishaBankAccount
