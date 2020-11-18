from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import Transition, register
from bluebottle.funding.states import BankAccountStateMachine
from bluebottle.funding.states import BasePaymentStateMachine
from bluebottle.funding_pledge.models import PledgeBankAccount
from bluebottle.funding_pledge.models import PledgePayment


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
