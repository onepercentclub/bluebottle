from django.db import transaction
from bluebottle.activity_pub.models import Event
from bluebottle.activity_pub.serializers import ActivityEventSerializer
from bluebottle.activity_pub.utils import get_platform_actor


class EventCreationService:
    """Service for creating Events and their related subevents from Activity"""
    
    @classmethod
    @transaction.atomic
    def create_activity_from_event(cls, data):
        subevents_data = data.pop('subevents', [])
        organizer = get_platform_actor()
        data.pop('resourcetype', None)
        event = Event.objects.create(organizer=organizer, **data)
        for subevent_data in subevents_data:
            Event.objects.create(parent=event, organizer=organizer, **subevent_data)
        return event
