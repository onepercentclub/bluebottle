from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.permissions import ActivityPermission, ActivityTypePermission
from bluebottle.events.filters import ParticipantListFilter
from bluebottle.events.models import Event, Participant
from bluebottle.events.serializers import (
    EventSerializer,
    EventTransitionSerializer,
    ParticipantSerializer,
    ParticipantTransitionSerializer
)
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.transitions.views import TransitionList

from bluebottle.utils.views import RetrieveUpdateAPIView, ListCreateAPIView, JsonApiViewMixin


class EventList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    permission_classes = (ActivityTypePermission, ActivityPermission,)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
    }

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class EventDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    permission_classes = (ActivityPermission,)

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
        'contributions': ['contributions'],
    }


class EventTransitionList(TransitionList):
    serializer_class = EventTransitionSerializer
    queryset = Event.objects.all()
    prefetch_for_includes = {
        'resource': ['event'],
    }


class ParticipantList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer

    filter_fields = ['activity__id', 'user__id']

    filter_backends = (
        ParticipantListFilter,
    )

    permission_classes = (
        ResourcePermission,
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user']
    }

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ParticipantDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class ParticipantTransitionList(TransitionList):
    serializer_class = ParticipantTransitionSerializer
    queryset = Participant.objects.all()
    prefetch_for_includes = {
        'resource': ['participant', 'participant__activity'],
    }
