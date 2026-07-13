from bluebottle.organizations.models import Organization

from bluebottle.activity_pub.effects import SyncEffect
from bluebottle.fsm.triggers import (
    TriggerManager, register, ModelChangedTrigger
)

@register(Organization)
class OrganizationTriggers(TriggerManager):
    triggers = [
        ModelChangedTrigger(
            ['start', 'end', 'description', 'title', 'image'],
            effects=[SyncEffect]
        ),
    ]
