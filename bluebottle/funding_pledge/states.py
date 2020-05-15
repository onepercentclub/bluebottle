from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import Transition
from bluebottle.funding.states import PaymentStateMachine
from bluebottle.funding_pledge.models import PledgePayment


class PledgePaymentStateMachine(PaymentStateMachine):
    model = PledgePayment

    request_refund = Transition(
        PaymentStateMachine.succeeded,
        PaymentStateMachine.refunded,
        name=_('Request refund'),
        automatic=False
    )
