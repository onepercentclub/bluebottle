from bluebottle.funding.states import BasePaymentStateMachine
from bluebottle.funding_telesom.models import TelesomPayment


class TelesomPaymentStateMachine(BasePaymentStateMachine):
    model = TelesomPayment

    request_refund = None
    refund_requested = None
