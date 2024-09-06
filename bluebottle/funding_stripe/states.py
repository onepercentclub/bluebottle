from django.utils.translation import gettext_lazy as _

from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.state import Transition, State, EmptyState
from bluebottle.fsm.state import register
from bluebottle.funding.states import BasePaymentStateMachine, PayoutAccountStateMachine, BankAccountStateMachine
from bluebottle.funding_stripe.models import StripePayment, StripeSourcePayment, StripePayoutAccount, ExternalAccount


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
    payments_disabled = State(
        _("payments disabled"),
        "payments_disabled",
        _("Payments are disabled for payout account."),
    )
    payouts_disabled = State(
        _("payouts disabled"),
        "payouts_disabled",
        _("Payouts are disabled for payout account."),
    )

    disable_payouts = Transition(
        [
            PayoutAccountStateMachine.new,
            PayoutAccountStateMachine.verified,
            PayoutAccountStateMachine.rejected,
        ],
        payouts_disabled,
        name=_("Disable payout account"),
        description=_("Payout account has been disabled"),
    )

    disable_payments = Transition(
        [
            PayoutAccountStateMachine.new,
            PayoutAccountStateMachine.verified,
            PayoutAccountStateMachine.rejected,
            payouts_disabled,
        ],
        payments_disabled,
        name=_("Disable payout account"),
        description=_("Payout account has been disabled"),
    )

    verify = Transition(
        [
            PayoutAccountStateMachine.new,
            PayoutAccountStateMachine.incomplete,
            PayoutAccountStateMachine.pending,
            payments_disabled,
            payouts_disabled,
        ],
        PayoutAccountStateMachine.verified,
        name=_("Verify"),
        description=_("Verify that the bank account is complete."),
        automatic=False,
    )


@register(ExternalAccount)
class StripeBankAccountStateMachine(BankAccountStateMachine):
    def account_verified(self):
        """the related connect account is verified"""
        return self.instance.connect_account and self.instance.connect_account.status == 'verified'

    initiate = Transition(
        EmptyState(),
        BankAccountStateMachine.unverified,
        name=_("Initiate"),
        description=_("Bank account details are entered.")
    )

    reject = Transition(
        [
            BankAccountStateMachine.verified,
            BankAccountStateMachine.unverified,
            BankAccountStateMachine.incomplete],
        BankAccountStateMachine.rejected,
        name=_('Reject'),
        description=_("Reject bank account"),
        automatic=True
    )

    verify = Transition(
        [
            BankAccountStateMachine.rejected,
            BankAccountStateMachine.incomplete,
            BankAccountStateMachine.unverified
        ],
        BankAccountStateMachine.verified,
        name=_('Verify'),
        description=_("Verify that the bank account is complete."),
        automatic=True
    )
