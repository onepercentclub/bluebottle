import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Event
from .serializers import EventSerializer
import logging

logger = logging.getLogger(__name__)


class EventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        logger.info("WebSocket connection attempt.")
        self.group_name = "events"
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        logger.info("WebSocket disconnected.")
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        logger.info("WebSocket received data.")
        # Handle incoming WebSocket messages
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')

        if action == 'get_latest_events':
            # Fetch latest events using sync-to-async
            instances = await self.get_latest_events()
            serializer = await self.serialize_events(instances)

            # Send serialized data back to WebSocket
            await self.send(text_data=json.dumps(serializer))

    async def send_instance(self, event):
        # Send serialized data to WebSocket
        instance = event['instance']
        await self.send(text_data=json.dumps(instance))

    @sync_to_async
    def get_latest_events(self):
        """
        Fetch the latest events from the database.
        """
        return Event.objects.all()

    @sync_to_async
    def serialize_events(self, instances):
        """
        Serialize the event instances.
        """
        serializer = EventSerializer(instances, many=True)
        return serializer.data
