from bluebottle.funding.states import BasePaymentStateMachine
from bluebottle.funding_flutterwave.models import FlutterwavePayment


class FlutterwavePaymentStateMachine(BasePaymentStateMachine):
    model = FlutterwavePayment

    request_refund = None
    refund_requested = None
