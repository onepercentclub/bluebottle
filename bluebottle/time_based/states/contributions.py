from bluebottle.activities.states import ContributionStateMachine
from bluebottle.fsm.state import register
from bluebottle.time_based.models import TimeContribution


@register(TimeContribution)
class TimeContributionStateMachine(ContributionStateMachine):
    pass
