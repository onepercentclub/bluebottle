from bluebottle.activities.effects import Complete
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger
from bluebottle.funding.models import Funding
from bluebottle.funding.states import FundingStateMachine


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


Funding.triggers = [Complete, DeadlineChanged, MatchingAmountChanged, AmountChanged]
