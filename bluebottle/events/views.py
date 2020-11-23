from django.http import HttpResponse
from django.utils.timezone import utc

from rest_framework_json_api.views import AutoPrefetchMixin

import icalendar

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission
)
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

from bluebottle.utils.views import (
    RetrieveUpdateAPIView, ListCreateAPIView, JsonApiViewMixin,
    PrivateFileView
)


class EventList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
    }

    def perform_create(self, serializer):
        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save(owner=self.request.user)


class EventDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer

    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'location': ['location'],
        'owner': ['owner'],
        'contributors': ['contributors'],
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


class EventIcalView(PrivateFileView):
    queryset = Event.objects.exclude(status__in=['cancelled', 'deleted', 'rejected'])

    max_age = 30 * 60  # half an hour

    def get(self, *args, **kwargs):
        instance = self.get_object()
        calendar = icalendar.Calendar()

        event = icalendar.Event()
        event.add('summary', instance.title)
        event.add('description', instance.details)
        event.add('url', instance.get_absolute_url())
        event.add('dtstart', instance.start.astimezone(utc))
        event.add('dtend', instance.end.astimezone(utc))
        event['uid'] = instance.uid

        organizer = icalendar.vCalAddress('MAILTO:{}'.format(instance.owner.email))
        organizer.params['cn'] = icalendar.vText(instance.owner.full_name)

        event['organizer'] = organizer
        if instance.location:
            event['location'] = icalendar.vText(instance.location.formatted_address)

        calendar.add_component(event)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.slug
        )

        return response
