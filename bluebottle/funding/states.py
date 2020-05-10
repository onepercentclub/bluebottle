from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from bluebottle.activities.states import ActivityStateMachine, ContributionStateMachine

from bluebottle.fsm.effects import (
    TransitionEffect,
    RelatedTransitionEffect,
    Effect
)
from bluebottle.fsm.state import Transition
from bluebottle.funding.models import Funding, Donation, Payout


class FundingStateMachine(ActivityStateMachine):

    model = Funding

    def should_finish(self):
        """the deadline has passed"""
        return self.instance.deadline and self.instance.deadline < timezone.now()

    def deadline_in_future(self):
        if not self.instance.deadline >= timezone.now():
            return _("The deadline of the activity should be in the future.")

    def target_reached(self):
        # FIXME!!!
        return True

    def target_not_reached(self):
        # FIXME!!!
        return False

    submit = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work
        ],
        ActivityStateMachine.submitted,
        name=_('Submit'),
        conditions=[
            ActivityStateMachine.is_complete,
            ActivityStateMachine.is_valid
        ],
        automatic=False
    )

    approve = Transition(
        [
            ActivityStateMachine.draft,
            ActivityStateMachine.needs_work,
            ActivityStateMachine.submitted,
            ActivityStateMachine.rejected
        ],
        ActivityStateMachine.open,
        name=_('Approve'),
        automatic=False,
        effects=[
            RelatedTransitionEffect('organizer', 'succeed'),
            TransitionEffect(
                'close',
                conditions=[should_finish]
            ),
        ]
    )


class DonationStateMachine(ContributionStateMachine):
    model = Donation


class PayoutStateMachine(ContributionStateMachine):
    model = Payout
