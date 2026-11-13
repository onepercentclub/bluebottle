from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from django.db.models import Q
from django.utils import timezone

from bluebottle.cta.models import ActionDismissal

SEVERITIES = {'urgent': 0, 'attention': 1, 'info': 2}


@dataclass
class ActionItem:
    type: str
    object_id: int
    group: str
    severity: str
    title: str
    message: str
    url: str
    count: int = 1
    created: Optional[datetime] = None
    is_demo: bool = False
    snoozed_until: Optional[datetime] = None
    meta: dict = field(default_factory=dict)

    @property
    def id(self):
        return '{}-{}'.format(self.type, self.object_id)


class ActionType(object):
    slug = None
    audience = 'manager'
    group = 'decision'
    priority = 50

    def get_items(self, user):
        raise NotImplementedError()


class Registry(object):
    def __init__(self):
        self.types = {}

    def register(self, action_type):
        self.types[action_type.slug] = action_type()
        return action_type

    def get(self, slug):
        return self.types.get(slug)

    def applicable(self, user):
        from bluebottle.cta.audience import audiences

        active = audiences(user)
        return [t for t in self.types.values() if t.audience in active]


registry = Registry()


def get_actions(user, include_snoozed=False):
    if not user.is_authenticated:
        return []

    now = timezone.now()
    dismissals = ActionDismissal.objects.filter(user=user).filter(
        Q(snoozed_until__isnull=True) | Q(snoozed_until__gt=now)
    )
    hidden = {(d.action_type, d.object_id): d.snoozed_until for d in dismissals}

    items = []
    for action_type in sorted(registry.applicable(user), key=lambda t: t.priority):
        for item in action_type.get_items(user):
            key = (item.type, item.object_id)
            if key not in hidden:
                items.append(item)
            elif include_snoozed and hidden[key]:
                item.snoozed_until = hidden[key]
                items.append(item)

    return sorted(
        items,
        key=lambda i: (i.snoozed_until is not None, SEVERITIES[i.severity], registry.get(i.type).priority)
    )


def dismiss(user, item_id, snooze_until=None):
    slug, _sep, object_id = item_id.rpartition('-')
    if not registry.get(slug) or not object_id.isdigit():
        return None

    dismissal, _created = ActionDismissal.objects.update_or_create(
        user=user,
        action_type=slug,
        object_id=int(object_id),
        defaults={'snoozed_until': snooze_until},
    )
    return dismissal
