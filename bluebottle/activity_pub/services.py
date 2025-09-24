from django.db import transaction

from bluebottle.activity_pub.models import Event, Place
from bluebottle.activity_pub.utils import get_platform_actor


class EventCreationService:
    """Service for creating Events and their related subevents from Activity"""

    @classmethod
    @transaction.atomic
    def create_event_from_activity(cls, data):
        subevents_data = data.pop('subevents', [])
        organizer = get_platform_actor()
        data.pop('resourcetype', None)
        place = data.pop('place', None)
        event = Event.objects.create(organizer=organizer, **data)
        for subevent_data in subevents_data:
            Event.objects.create(parent=event, organizer=organizer, **subevent_data)

        if place:
            place.pop('_custom_context', None)
            place.pop('type', None)
            event.place = Place.objects.create(**place)
            event.save()

        return event
