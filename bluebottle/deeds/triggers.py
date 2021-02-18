from bluebottle.activities.states import OrganizerStateMachine
from bluebottle.activities.triggers import (
    ActivityTriggers
)
from bluebottle.deeds.models import Deed
from bluebottle.fsm.effects import RelatedTransitionEffect
from bluebottle.fsm.triggers import (
    register, TransitionTrigger
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.effects import (
    ActiveTimeContributionsTransitionEffect
)
from bluebottle.time_based.messages import (
    ActivitySucceededNotification, ActivityExpiredNotification, ActivityRejectedNotification,
    ActivityCancelledNotification
)
from bluebottle.time_based.states import (
    TimeBasedStateMachine, TimeContributionStateMachine
)


@register(Deed)
class DeedTriggers(ActivityTriggers):
    triggers = ActivityTriggers.triggers + [
        TransitionTrigger(
            TimeBasedStateMachine.succeed,
            effects=[
                NotificationEffect(ActivitySucceededNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.succeed)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.reject,
            effects=[
                NotificationEffect(ActivityRejectedNotification),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),
        TransitionTrigger(
            TimeBasedStateMachine.cancel,
            effects=[
                NotificationEffect(ActivityCancelledNotification),
                RelatedTransitionEffect('organizer', OrganizerStateMachine.fail),
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.fail)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.restore,
            effects=[
                ActiveTimeContributionsTransitionEffect(TimeContributionStateMachine.reset)
            ]
        ),

        TransitionTrigger(
            TimeBasedStateMachine.expire,
            effects=[
                NotificationEffect(ActivityExpiredNotification),
            ]
        ),
    ]
