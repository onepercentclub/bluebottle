from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import Transition
from bluebottle.fsm.state import register
from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_pledge.models import PledgePayment, PledgeBankAccount


@register(PledgePayment)
class PledgePaymentStateMachine(BasePaymentStateMachine):
    pending = None

    request_refund = Transition(
        BasePaymentStateMachine.succeeded,
        BasePaymentStateMachine.refunded,
        name=_('Request refund'),
        automatic=False
    )


@register(PledgeBankAccount)
class PledgeBankAccountStateMachine(BankAccountStateMachine):
    pass
