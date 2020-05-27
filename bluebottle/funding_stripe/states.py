from bluebottle.fsm.effects import RelatedTransitionEffect
from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.state import Transition, State
from bluebottle.funding.effects import RefundPaymentAtPSP
from bluebottle.funding.states import BasePaymentStateMachine
from bluebottle.funding_stripe.effects import RefundStripePaymentAtPSP
from bluebottle.funding_stripe.models import StripePayment, StripeSourcePayment


class StripePaymentStateMachine(BasePaymentStateMachine):
    model = StripePayment

    request_refund = Transition(
        BasePaymentStateMachine.succeeded,
        BasePaymentStateMachine.refund_requested,
        name=_('Request refund'),
        automatic=False,
        effects=[
            RefundStripePaymentAtPSP
        ]
    )


class StripeSourcePaymentStateMachine(BasePaymentStateMachine):

    model = StripeSourcePayment

    charged = State(_('charged'), 'charged')
    canceled = State(_('canceled'), 'canceled')
    disputed = State(_('disputed'), 'disputed')

    def has_charge_token(self):
        return bool(self.instance.charge_token)

    def is_not_refunded(self):
        return self.instance.status not in ['refunded', 'disputed']

    authorize = Transition(
        charged,
        BasePaymentStateMachine.pending,
        name=_('Authorize'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'succeed')
        ]
    )

    succeed = Transition(
        [
            BasePaymentStateMachine.new,
            BasePaymentStateMachine.pending,
            charged
        ],
        BasePaymentStateMachine.succeeded,
        name=_('Succeed'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'succeed')
        ]
    )

    charge = Transition(
        BasePaymentStateMachine.new,
        charged,
        name=_('Charge'),
        automatic=True,
        conditions=[has_charge_token]
    )

    cancel = Transition(
        BasePaymentStateMachine.new,
        canceled,
        name=_('Canceled'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'fail')
        ]
    )

    dispute = Transition(
        BasePaymentStateMachine.succeeded,
        disputed,
        name=_('Dispute'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'refund')
        ]
    )

    request_refund = Transition(
        BasePaymentStateMachine.succeeded,
        BasePaymentStateMachine.refund_requested,
        name=_('Request refund'),
        automatic=False,
        effects=[
            RefundPaymentAtPSP
        ]
    )
