from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger,
    ModelChangedTrigger,
    register,
    TriggerManager,
)
from bluebottle.funding.messages import (
    PayoutAccountVerified,
    PayoutAccountRejected,
    LivePayoutAccountRejected,
)
from bluebottle.funding.models import Funding
from bluebottle.funding.states import DonorStateMachine, PayoutAccountStateMachine
from bluebottle.funding.triggers import BasePaymentTriggers
from bluebottle.funding_stripe.models import (
    StripeSourcePayment,
    StripePayoutAccount,
    ExternalAccount,
)
from bluebottle.funding_stripe.states import (
    StripePayoutAccountStateMachine,
    StripeSourcePaymentStateMachine,
    StripeBankAccountStateMachine,
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.funding_stripe.effects import PutActivitiesOnHoldEffect


@register(StripeSourcePayment)
class StripeSourcePaymentTriggers(BasePaymentTriggers):
    triggers = BasePaymentTriggers.triggers + [
        TransitionTrigger(
            StripeSourcePaymentStateMachine.authorize,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            StripeSourcePaymentStateMachine.succeed,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            StripeSourcePaymentStateMachine.cancel,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            StripeSourcePaymentStateMachine.dispute,
            effects=[
                RelatedTransitionEffect('donation', DonorStateMachine.refund)
            ]
        ),
    ]


def has_live_campaign(effect):
    """has connected funding activity that is open"""
    live_statuses = ["open", "on_hold"]

    return (
        Funding.objects.filter(bank_account__connect_account=effect.instance)
        .filter(status__in=live_statuses)
        .exists()
    )


@register(StripePayoutAccount)
class StripePayoutAccountTriggers(TriggerManager):
    def account_verified(self):
        """the connect account is verified"""
        return self.instance.verified

    def account_not_verified(self):
        """the connect account is not verified"""
        return not self.instance.verified

    def payments_disabled(self):
        """the payments are disabled"""
        return not self.instance.payments_enabled

    def payouts_disabled(self):
        """the payouts are disabled"""
        return not self.instance.payouts_enabled

    def complete(self):
        """The connect account is verified"""
        return self.instance.payments_enabled and self.instance.payouts_enabled

    triggers = [
        TransitionTrigger(
            StripePayoutAccountStateMachine.verify,
            effects=[
                NotificationEffect(PayoutAccountVerified),
                RelatedTransitionEffect(
                    'external_accounts',
                    StripeBankAccountStateMachine.verify
                )
            ]
        ),
        TransitionTrigger(
            StripePayoutAccountStateMachine.reject,
            effects=[
                NotificationEffect(PayoutAccountRejected),
            ],
        ),
        TransitionTrigger(
            StripePayoutAccountStateMachine.disable_payments,
            effects=[
                NotificationEffect(PayoutAccountRejected),
                PutActivitiesOnHoldEffect,
                NotificationEffect(
                    LivePayoutAccountRejected, conditions=[has_live_campaign]
                ),
                RelatedTransitionEffect(
                    "external_accounts", StripeBankAccountStateMachine.reject
                ),
            ],
        ),
        TransitionTrigger(
            StripePayoutAccountStateMachine.disable_payouts,
            effects=[
                NotificationEffect(PayoutAccountRejected),
                RelatedTransitionEffect(
                    "external_accounts", StripeBankAccountStateMachine.reject
                ),
            ],
        ),
        ModelChangedTrigger(
            ["verified", "payouts_enabled", "payments_enabled"],
            effects=[
                TransitionEffect(
                    StripePayoutAccountStateMachine.verify,
                    conditions=[complete, account_verified],
                ),
            ],
        ),
        ModelChangedTrigger(
            ["payouts_enabled"],
            effects=[
                TransitionEffect(
                    StripePayoutAccountStateMachine.disable_payouts,
                    conditions=[payouts_disabled],
                ),
            ],
        ),
        ModelChangedTrigger(
            ["payments_enabled"],
            effects=[
                TransitionEffect(
                    StripePayoutAccountStateMachine.disable_payments,
                    conditions=[payments_disabled],
                ),
            ],
        ),
        ModelChangedTrigger(
            ["verified"],
            effects=[
                TransitionEffect(
                    StripePayoutAccountStateMachine.reject,
                    conditions=[account_not_verified],
                )
            ],
        ),
    ]


@register(ExternalAccount)
class StripeBankAccountTriggers(TriggerManager):
    def account_verified(effect):
        """connected payout account is verified"""
        return (
            effect.instance.connect_account
            and effect.instance.connect_account.status
            == PayoutAccountStateMachine.verified.value
        )

    triggers = [
        TransitionTrigger(
            StripeBankAccountStateMachine.initiate,
            effects=[
                TransitionEffect(
                    StripeBankAccountStateMachine.verify,
                    conditions=[
                        account_verified
                    ]
                )
            ]
        )
    ]
