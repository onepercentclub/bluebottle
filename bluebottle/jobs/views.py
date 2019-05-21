from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission

from bluebottle.utils.views import RetrieveUpdateAPIView, ListCreateAPIView
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)

from bluebottle.events.models import Event, Participant
from bluebottle.events.serializers import EventSerializer, ParticipantSerializer


class EventList(ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)


class EventDetail(RetrieveUpdateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    lookup_field = 'slug'

    permission_classes = (ActivityTypePermission, ActivityPermission,)


class ParticipantList(ListCreateAPIView):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class ParticipantDetail(RetrieveUpdateAPIView):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer

    lookup_field = 'slug'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
