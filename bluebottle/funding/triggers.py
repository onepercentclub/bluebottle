from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger
from bluebottle.funding.models import Funding, PlainPayoutAccount
from bluebottle.funding.states import FundingStateMachine, PlainPayoutAccountStateMachine


class DeadlineChanged(ModelChangedTrigger):
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
            'close',
            conditions=[
                FundingStateMachine.should_finish,
                FundingStateMachine.no_donations
            ]
        ),
    ]


class AmountChanged(ModelChangedTrigger):
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
            'close',
            conditions=[FundingStateMachine.should_finish, FundingStateMachine.no_donations]
        ),
    ]


class MatchingAmountChanged(AmountChanged):
    field = 'amount_matching'


Funding.triggers = [DeadlineChanged, MatchingAmountChanged, AmountChanged]


class AccountReviewed(ModelChangedTrigger):
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


PlainPayoutAccount.triggers = [AccountReviewed]
