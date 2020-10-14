from bluebottle.fsm.triggers import register
from bluebottle.time_based.models import OnADateActivity, WithADeadlineActivity, OngoingActivity
from bluebottle.activities.triggers import ActivityTriggers


@register(OnADateActivity)
class OnADateTriggers(ActivityTriggers):
    pass


@register(WithADeadlineActivity)
class WithADeadlineTriggers(ActivityTriggers):
    pass


@register(OngoingActivity)
class OngoingTriggers(ActivityTriggers):
    pass
