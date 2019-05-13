from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.permissions import ActivityPermission
from bluebottle.events.models import Event, Participant
from bluebottle.events.serializers import EventSerializer, ParticipantSerializer
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission)
from bluebottle.utils.views import RetrieveUpdateAPIView, ListCreateAPIView, JsonApiViewMixin


class EventList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    permission_classes = (ActivityPermission,)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'image': ['image']
    }

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class EventDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    lookup_field = 'slug'

    permission_classes = (
        ActivityPermission,
    )


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
