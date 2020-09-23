from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger
from bluebottle.funding.effects import UpdateFundingAmountsEffect
from bluebottle.funding.models import Funding, PlainPayoutAccount, Donation
from bluebottle.funding.states import FundingStateMachine, PlainPayoutAccountStateMachine


class DeadlineChangedTrigger(ModelChangedTrigger):
    field = 'deadline'

    effects = [
        TransitionEffect(
            'extend',
            conditions=[
                FundingStateMachine.is_complete,
                FundingStateMachine.is_valid,
                FundingStateMachine.deadline_in_future,
                FundingStateMachine.without_approved_payouts
            ]
        ),
        TransitionEffect(
            'succeed',
            conditions=[
                FundingStateMachine.should_finish,
                FundingStateMachine.target_reached
            ]
        ),
        TransitionEffect(
            'partial',
            conditions=[
                FundingStateMachine.should_finish,
                FundingStateMachine.target_not_reached
            ]
        ),
        TransitionEffect(
            'cancel',
            conditions=[
                FundingStateMachine.should_finish,
                FundingStateMachine.no_donations
            ]
        ),
    ]


class AmountChangedTrigger(ModelChangedTrigger):
    field = 'target'

    effects = [
        TransitionEffect(
            'succeed',
            conditions=[FundingStateMachine.should_finish, FundingStateMachine.target_reached]
        ),
        TransitionEffect(
            'partial',
            conditions=[FundingStateMachine.should_finish, FundingStateMachine.target_not_reached]
        ),
        TransitionEffect(
            'cancel',
            conditions=[FundingStateMachine.should_finish, FundingStateMachine.no_donations]
        ),
    ]


class MatchingAmountChangedTrigger(AmountChangedTrigger):
    field = 'amount_matching'


Funding.triggers = [DeadlineChangedTrigger, MatchingAmountChangedTrigger, AmountChangedTrigger]


class AccountReviewedTrigger(ModelChangedTrigger):
    field = 'reviewed'

    effects = [
        TransitionEffect(
            'verify',
            conditions=[PlainPayoutAccountStateMachine.is_reviewed]
        ),
        TransitionEffect(
            'reject',
            conditions=[PlainPayoutAccountStateMachine.is_unreviewed]
        ),
    ]


PlainPayoutAccount.triggers = [AccountReviewedTrigger]


class DonationAmountChangedTrigger(ModelChangedTrigger):
    field = 'payout_amount'

    effects = [
        UpdateFundingAmountsEffect
    ]


Donation.triggers = [DonationAmountChangedTrigger]
