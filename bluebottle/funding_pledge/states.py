from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import Transition
from bluebottle.funding.states import BasePaymentStateMachine
from bluebottle.funding_pledge.models import PledgePayment


class PledgeBasePaymentStateMachine(BasePaymentStateMachine):
    model = PledgePayment

    request_refund = Transition(
        BasePaymentStateMachine.succeeded,
        BasePaymentStateMachine.refunded,
        name=_('Request refund'),
        automatic=False
    )
