import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Event
from .serializers import EventSerializer
import logging
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

from .views import EventListView
from ..bluebottle_drf2.renderers import BluebottleJSONAPIRenderer

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
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')

        if action == 'get_latest_events':
            instances = await self.get_latest_events()
            data = await self.serialize_events(instances)

            data['message'] = 'latest_events'
            await self.send(text_data=json.dumps(data))

    async def send_event(self, event):
        # Send serialized data to WebSocket
        instance = event['instance']
        data = await self.serialize_events([instance])
        data['message'] = 'new_event'
        await self.send(text_data=json.dumps(data))

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
        context = {
            'view': EventListView(),
            'request': Request(APIRequestFactory().get('/'))
        }
        serializer = EventSerializer(instance=instances, many=True, context=context)
        renderer = BluebottleJSONAPIRenderer()
        data = renderer.render(
            serializer.data,
            'application/vnd.api+json',
            context
        )
        return json.loads(data)
