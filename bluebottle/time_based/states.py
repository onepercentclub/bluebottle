from bluebottle.activities.states import ActivityStateMachine
from bluebottle.time_based.models import OnADateActivity, WithADeadlineActivity, OngoingActivity
from bluebottle.fsm.state import register


@register(OnADateActivity)
class OnADateStateMachine(ActivityStateMachine):
    pass


@register(WithADeadlineActivity)
class WithADeadlineStateMachine(ActivityStateMachine):
    pass


@register(OngoingActivity)
class OngoingStateMachine(ActivityStateMachine):
    pass
