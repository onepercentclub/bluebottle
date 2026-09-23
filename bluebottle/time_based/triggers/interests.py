from bluebottle.fsm.triggers import (
    ModelCreatedTrigger,
    TriggerManager,
    register,
)
from bluebottle.notifications.effects import NotificationEffect
from bluebottle.time_based.messages.messages import InterestRegisteredNotification
from bluebottle.time_based.models import Interest


@register(Interest)
class InterestTriggers(TriggerManager):
    triggers = [
        ModelCreatedTrigger(
            effects=[
                NotificationEffect(InterestRegisteredNotification),
            ]
        ),
    ]
