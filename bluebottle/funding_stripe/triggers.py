from bluebottle.fsm.effects import RelatedTransitionEffect, TransitionEffect
from bluebottle.fsm.triggers import (
    TransitionTrigger,
    ModelChangedTrigger,
    register,
    TriggerManager,
)
from bluebottle.funding.messages import (
    PayoutAccountVerified,
    PayoutAccountMarkedIncomplete,
    LivePayoutAccountMarkedIncomplete,
)
from bluebottle.funding.models import Funding
from bluebottle.funding.states import DonorStateMachine, PayoutAccountStateMachine
from bluebottle.funding.triggers import BasePaymentTriggers
from bluebottle.funding_stripe.effects import PutActivitiesOnHoldEffect, AcceptTosEffect
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


@register(StripePayoutAccount)
class StripePayoutAccountTriggers(TriggerManager):
    def has_live_campaign(effect):
        """has connected funding activity that is open"""
        live_statuses = ["open", "on_hold"]

        return (
            Funding.objects.filter(bank_account__connect_account=effect.instance)
            .filter(status__in=live_statuses)
            .exists()
        )

    def account_verified(self):
        """the connect account is verified"""
        return (
            self.instance.verified
            and self.instance.payments_enabled
            and self.instance.payouts_enabled
        )

    def account_not_verified(self):
        """the connect account is not verified"""

        return not self.account_verified()

    def is_complete(self):
        """The connect account is verified"""
        return self.instance.requirements == []

    def is_not_complete(self):
        """The connect account is verified"""
        return (not self.instance.requirements == [])

    def payments_are_disabled(self):
        """The connect account is verified"""
        return not self.instance.payments_enabled

    def has_new_requirements(self):
        """The connect account is verified"""
        initial_requirements = self.instance._initial_values["requirements"]

        return len(
            [
                requirement
                for requirement in self.instance.requirements
                if requirement not in initial_requirements
            ]
        )

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
            StripePayoutAccountStateMachine.set_incomplete,
            effects=[
                NotificationEffect(
                    PayoutAccountMarkedIncomplete,
                ),
                NotificationEffect(
                    LivePayoutAccountMarkedIncomplete,
                    conditions=[has_live_campaign],
                ),
                TransitionEffect(
                    StripePayoutAccountStateMachine.disable,
                    conditions=[payments_are_disabled],
                ),
            ],
        ),
        TransitionTrigger(
            StripePayoutAccountStateMachine.disable,
            effects=[PutActivitiesOnHoldEffect],
        ),
        ModelChangedTrigger(
            ["verified", "requirements"],
            effects=[
                TransitionEffect(
                    StripePayoutAccountStateMachine.verify,
                    conditions=[is_complete, account_verified],
                ),
                TransitionEffect(
                    StripePayoutAccountStateMachine.set_incomplete,
                    conditions=[is_not_complete],
                ),
            ],
        ),
        ModelChangedTrigger(
            ["requirements"],
            effects=[
                TransitionEffect(
                    StripePayoutAccountStateMachine.set_incomplete,
                    conditions=[has_new_requirements],
                ),
                TransitionEffect(
                    StripePayoutAccountStateMachine.submit,
                    conditions=[is_complete],
                ),
            ],
        ),
        ModelChangedTrigger(
            ["tos_accepted"],
            effects=[
                AcceptTosEffect,
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
