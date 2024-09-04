
from bluebottle.fsm.triggers import (
    TriggerManager, register, ModelCreatedTrigger
)
from bluebottle.notifications.effects import NotificationEffect

from bluebottle.updates.models import Update
from bluebottle.updates.messages import FollowersNotification, OwnerNotification, ParentNotification


def should_notify(effect):
    return effect.instance.notify


def author_is_not_owner(effect):
    return effect.instance.author != effect.instance.activity.owner


def has_parent(effect):
    return effect.instance.parent is not None

def has_no_contribution(effect):
    return effect.instance.contribution is None

@register(Update)
class UpdateTriggers(TriggerManager):
    triggers = [
        ModelCreatedTrigger(
            effects=[
                NotificationEffect(
                    FollowersNotification,
                    conditions=[should_notify]
                ),
                NotificationEffect(
                    OwnerNotification,
                    conditions=[author_is_not_owner, has_no_contribution],
                ),
                NotificationEffect(
                    ParentNotification,
                    conditions=[has_parent]
                )
            ]
        )
    ]
