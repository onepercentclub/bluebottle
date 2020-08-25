from bluebottle.funding.states import BasePaymentStateMachine
from bluebottle.funding_lipisha.models import LipishaPayment


class LipishaPaymentStateMachine(BasePaymentStateMachine):
    model = LipishaPayment

    request_refund = None
    refund_requested = None
