from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.utils.translation import gettext_lazy as _

from bluebottle.events.models import Event
from bluebottle.events.serializers import EventSerializer
from bluebottle.fsm.effects import Effect


class BaseTriggerEventEffect(Effect):
    title = _('Trigger event')
    template = 'admin/notification_effect.html'

    def post_save(self):
        event = Event(type=self.type, content_object=self.instance)

        event.save()

    def __str__(self):
        return _(f'Trigger {self.type}')


def TriggerEvent(type, conditions=None):
    _type = type
    _conditions = conditions

    class _TriggerEventEffect(BaseTriggerEventEffect):
        type = _type
        conditions = _conditions or []

    return _TriggerEventEffect


class SendEventEffect(Effect):
    def post_save(self):
        instance = self.instance
        channel_layer = get_channel_layer()
        serializer = EventSerializer(instance)
        async_to_sync(channel_layer.group_send)(
            "events",
            {
                "type": "send_event",
                "instance": serializer.data,
            }
        )
