from django.http import HttpResponse
from django.utils.html import strip_tags
from django.utils.timezone import utc

import icalendar

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ContributorPermission
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant
)
from bluebottle.time_based.serializers import (
    DateActivitySerializer,
    PeriodActivitySerializer,
    DateTransitionSerializer,
    PeriodTransitionSerializer,
    PeriodParticipantSerializer,
    DateParticipantSerializer,
    DateParticipantTransitionSerializer,
    PeriodParticipantTransitionSerializer
)

from bluebottle.transitions.views import TransitionList

from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, ListCreateAPIView, JsonApiViewMixin,
    PrivateFileView
)


class TimeBasedActivityListView(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

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


class TimeBasedActivityDetailView(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )


class DateActivityListView(TimeBasedActivityListView):
    queryset = DateActivity.objects.all()
    serializer_class = DateActivitySerializer


class PeriodActivityListView(TimeBasedActivityListView):
    queryset = PeriodActivity.objects.all()
    serializer_class = PeriodActivitySerializer


class DateActivityDetailView(TimeBasedActivityDetailView):
    queryset = DateActivity.objects.all()
    serializer_class = DateActivitySerializer


class PeriodActivityDetailView(TimeBasedActivityDetailView):
    queryset = PeriodActivity.objects.all()
    serializer_class = PeriodActivitySerializer


class DateTransitionList(TransitionList):
    serializer_class = DateTransitionSerializer
    queryset = DateActivity.objects.all()


class PeriodTransitionList(TransitionList):
    serializer_class = PeriodTransitionSerializer
    queryset = PeriodActivity.objects.all()


class ParticipantList(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    prefetch_for_includes = {
        'assignment': ['assignment'],
        'user': ['user'],
        'document': ['document'],
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

        serializer.save(user=self.request.user)


class DateParticipantList(ParticipantList):
    queryset = DateParticipant.objects.all()
    serializer_class = DateParticipantSerializer


class PeriodParticipantList(ParticipantList):
    queryset = PeriodParticipant.objects.all()
    serializer_class = PeriodParticipantSerializer


class ParticipantDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user'],
        'document': ['document'],
    }


class DateParticipantDetail(ParticipantDetail):
    queryset = DateParticipant.objects.all()
    serializer_class = DateParticipantSerializer


class PeriodParticipantDetail(ParticipantDetail):
    queryset = PeriodParticipant.objects.all()
    serializer_class = PeriodParticipantSerializer


class ParticipantTransitionList(TransitionList):
    prefetch_for_includes = {
        'resource': ['participant', 'participant__activity'],
    }


class DateParticipantTransitionList(ParticipantTransitionList):
    serializer_class = DateParticipantTransitionSerializer
    queryset = DateParticipant.objects.all()


class PeriodParticipantTransitionList(ParticipantTransitionList):
    serializer_class = PeriodParticipantTransitionSerializer
    queryset = PeriodParticipant.objects.all()


class ParticipantDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    queryset = DateParticipant.objects
    relation = 'document'
    field = 'file'


class DateParticipantDocumentDetail(ParticipantDocumentDetail):
    queryset = DateParticipant.objects


class PeriodParticipantDocumentDetail(ParticipantDocumentDetail):
    queryset = PeriodParticipant.objects


class DateActivityIcalView(PrivateFileView):
    queryset = DateActivity.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected']
    )

    max_age = 30 * 60  # half an hour

    def get(self, *args, **kwargs):
        instance = self.get_object()
        calendar = icalendar.Calendar()

        event = icalendar.Event()
        event.add('summary', instance.title)
        event.add(
            'description',
            u'{}\n{}'.format(strip_tags(instance.description), instance.get_absolute_url())
        )
        event.add('url', instance.get_absolute_url())
        event.add('dtstart', instance.start.astimezone(utc))
        event.add('dtend', (instance.start + instance.duration).astimezone(utc))
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
