from bluebottle.members.models import Member

from bluebottle.activity_pub.effects import SyncEffect
from bluebottle.fsm.triggers import (
    TriggerManager, register, ModelChangedTrigger
)


@register(Member)
class MemberTriggers(TriggerManager):
    triggers = [
        ModelChangedTrigger(
            ['first_name', 'last_name', 'email'],
            effects=[SyncEffect]
        ),
    ]
