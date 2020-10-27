from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import Transition
from bluebottle.funding.states import BasePaymentStateMachine, BankAccountStateMachine
from bluebottle.funding_pledge.models import PledgePayment, PledgeBankAccount


class PledgePaymentStateMachine(BasePaymentStateMachine):
    model = PledgePayment
    pending = None

    request_refund = Transition(
        BasePaymentStateMachine.succeeded,
        BasePaymentStateMachine.refunded,
        name=_('Request refund'),
        automatic=False
    )


class PledgeBankAccountStateMachine(BankAccountStateMachine):
    model = PledgeBankAccount
