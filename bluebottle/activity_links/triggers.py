from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_links.states import LinkedActivityStateMachine
from bluebottle.activity_pub.effects import PublishAdoptionEffect
from bluebottle.fsm.triggers import (
    TriggerManager, TransitionTrigger, register
)


@register(LinkedActivity)
class LinkedActivityTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            LinkedActivityStateMachine.initiate,
            effects=[PublishAdoptionEffect]
        ),
    ]
