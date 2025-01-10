from datetime import date

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
    ScheduleActivity,
    TimeContribution, DeadlineActivity
)
from bluebottle.time_based.states import (
    TimeContributionStateMachine
)


def should_succeed_instantly(effect):
    """
    contribution (slot) has finished
    """
    activity = effect.instance.contributor.activity
    if (
        effect.instance.contribution_type == 'preparation' and
        effect.instance.contributor.status in ('accepted', 'succeeded')
    ):
        return True
    elif (
        isinstance(activity, PeriodActivity) and
        effect.instance.contributor.status in ('accepted', 'succeeded')
    ):
        return True
    elif (
        isinstance(activity, DeadlineActivity) and
        effect.instance.contributor.registration and
        effect.instance.contributor.registration.status == 'accepted'
    ):
        if (
            not effect.instance.contributor.activity.start or
            effect.instance.contributor.activity.start <= date.today()
        ):
            return True
        return False
    elif isinstance(activity, ScheduleActivity):
        return False

    return (
        (
            effect.instance.end is None or
            effect.instance.end < now()
        ) and
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
