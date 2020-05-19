from bluebottle.funding.states import BasePaymentStateMachine
from bluebottle.funding_vitepay.models import VitepayPayment


class VitepayPaymentStateMachine(BasePaymentStateMachine):
    model = VitepayPayment
