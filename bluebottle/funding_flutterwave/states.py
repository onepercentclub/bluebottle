from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwaveBankAccount


class FlutterwavePaymentStateMachine(BasePaymentStateMachine):
    model = FlutterwavePayment

    request_refund = None
    refund_requested = None


class FlutterwaveBankAccountStateMachine(BankAccountStateMachine):
    model = FlutterwaveBankAccount
