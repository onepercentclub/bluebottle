from bluebottle.activity_links.models import LinkedActivity
from bluebottle.activity_links.states import LinkedActivityStateMachine
from bluebottle.activity_pub.effects import PublishAdoptionEffect, UnpublishAdoptionEffect
from bluebottle.fsm.triggers import (
    TriggerManager, TransitionTrigger, register
)


@register(LinkedActivity)
class LinkedActivityTriggers(TriggerManager):
    triggers = [
        TransitionTrigger(
            LinkedActivityStateMachine.start,
            effects=[PublishAdoptionEffect]
        ),
        TransitionTrigger(
            LinkedActivityStateMachine.succeed,
            effects=[PublishAdoptionEffect]
        ),
        TransitionTrigger(
            LinkedActivityStateMachine.cancel,
            effects=[UnpublishAdoptionEffect]
        ),
    ]
