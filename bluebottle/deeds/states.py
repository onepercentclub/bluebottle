from bluebottle.activities.states import ActivityStateMachine
from bluebottle.deeds.models import Deed
from bluebottle.fsm.state import register


@register(Deed)
class DeedStateMachine(ActivityStateMachine):
    pass
