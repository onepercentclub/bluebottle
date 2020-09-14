from django.utils.translation import ugettext_lazy as _

from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.state import Transition, State, register
from bluebottle.funding.states import BasePaymentStateMachine, PayoutAccountStateMachine
from bluebottle.funding_stripe.models import StripePayment, StripeSourcePayment, StripePayoutAccount


@register(StripePayment)
class StripePaymentStateMachine(BasePaymentStateMachine):
    pass


@register(StripeSourcePayment)
class StripeSourcePaymentStateMachine(BasePaymentStateMachine):
    charged = State(_('charged'), 'charged')
    canceled = State(_('canceled'), 'canceled')
    disputed = State(_('disputed'), 'disputed')

    def has_charge_token(self):
        return bool(self.instance.charge_token)

    def is_not_refunded(self):
        return self.instance.status not in ['refunded', 'disputed']

    authorize = Transition(
        [
            BasePaymentStateMachine.new,
            charged
        ],
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
        [
            BasePaymentStateMachine.new,
            BasePaymentStateMachine.succeeded,
        ],
        disputed,
        name=_('Dispute'),
        automatic=True,
        effects=[
            RelatedTransitionEffect('donation', 'refund')
        ]
    )


@register(StripePayoutAccount)
class StripePayoutAccountStateMachine(PayoutAccountStateMachine):
    pass
