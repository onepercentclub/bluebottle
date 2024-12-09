from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from bluebottle.events.serializers import EventSerializer
from bluebottle.fsm.effects import Effect


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
