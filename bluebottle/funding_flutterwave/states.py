from bluebottle.funding.states import BasePaymentStateMachine
from bluebottle.funding_flutterwave.models import FlutterwavePayment


class FlutterwavePaymentStateMachine(BasePaymentStateMachine):
    model = FlutterwavePayment
