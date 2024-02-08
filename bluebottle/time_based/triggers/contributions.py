from django.utils.timezone import now

from bluebottle.activities.triggers import (
    ContributionTriggers
)
from bluebottle.fsm.effects import TransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger
)
from bluebottle.time_based.models import (
    PeriodActivity,
    TimeContribution
)
from bluebottle.time_based.states import (
    TimeContributionStateMachine
)


def should_succeed_instantly(effect):
    """
    contribution (slot) has finished
    """
    activity = effect.instance.contributor.activity
    if effect.instance.contribution_type == 'preparation':
        if effect.instance.contributor.status in ('accepted',):
            return True
        else:
            return False
    elif isinstance(activity, PeriodActivity):
        return True
    return (
        (effect.instance.end is None or effect.instance.end < now()) and
        effect.instance.contributor.status in ('accepted', 'succeeded') and
        effect.instance.contributor.activity.status in ('open', 'succeeded')
    )


@register(TimeContribution)
class TimeContributionTriggers(ContributionTriggers):
    triggers = ContributionTriggers.triggers + [
        TransitionTrigger(
            TimeContributionStateMachine.reset,
            effects=[
                TransitionEffect(
                    TimeContributionStateMachine.succeed,
                    conditions=[
                        should_succeed_instantly
                    ]),
            ]
        ),

        TransitionTrigger(
            TimeContributionStateMachine.initiate,
            effects=[
                TransitionEffect(
                    TimeContributionStateMachine.succeed,
                    conditions=[
                        should_succeed_instantly
                    ]),
            ]
        ),

    ]
