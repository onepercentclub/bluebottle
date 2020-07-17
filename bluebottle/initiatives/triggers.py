from bluebottle.fsm.triggers import ModelChangedTrigger
from bluebottle.initiatives.messages import AssignedReviewerMessage
from bluebottle.initiatives.models import Initiative
from bluebottle.notifications.effects import NotificationEffect


class AssignedReviewerTrigger(ModelChangedTrigger):
    field = 'reviewer'

    effects = [
        NotificationEffect(AssignedReviewerMessage)
    ]


Initiative.triggers = [AssignedReviewerTrigger]
