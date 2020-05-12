from django.utils import timezone

from bluebottle.activities.effects import Complete
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import ModelChangedTrigger
from bluebottle.funding.models import Funding
from bluebottle.funding.states import FundingStateMachine


class Finished(ModelChangedTrigger):
    @property
    def is_valid(self):
        return (
            self.instance.deadline and
            self.instance.deadline < timezone.now() and
            self.instance.status not in ('succeeded', 'closed', )
        )

    effects = [
        TransitionEffect(
            'succeed',
            conditions=[FundingStateMachine.should_finish, FundingStateMachine.target_reached]
        ),
        TransitionEffect(
            'close',
            conditions=[FundingStateMachine.should_finish, FundingStateMachine.target_not_reached]
        ),
    ]


Funding.triggers = [Complete, Finished]