from django.db.models import Q
from django.http import HttpResponse
from django.utils.html import strip_tags
from django.utils.timezone import utc

import icalendar

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ContributionPermission, DeleteActivityPermission
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    OnADateApplication, PeriodApplication
)
from bluebottle.time_based.serializers import (
    DateActivitySerializer,
    PeriodActivitySerializer,
    DateTransitionSerializer,
    PeriodTransitionSerializer,
    PeriodApplicationSerializer,
    OnADateApplicationSerializer,
    OnADateApplicationTransitionSerializer,
    PeriodApplicationTransitionSerializer
)

from bluebottle.transitions.views import TransitionList

from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView,
    ListAPIView, JsonApiViewMixin,
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


class TimeBasedActivityDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
        DeleteActivityPermission
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


class TimeBasedActivityRelatedApplicationsList(JsonApiViewMixin, ListAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        if self.request.user.is_authenticated():
            queryset = self.queryset.filter(
                Q(user=self.request.user) |
                Q(activity__owner=self.request.user) |
                Q(activity__initiative__activity_manager=self.request.user) |
                Q(status__in=[
                    'new', 'accepted', 'succeeded'
                ])
            )
        else:
            queryset = self.queryset.filter(
                status__in=[
                    'new', 'accepted', 'succeeded'
                ])

        return queryset.filter(
            activity_id=self.kwargs['activity_id']
        )


class DateActivityRelatedApplicationsList(TimeBasedActivityRelatedApplicationsList):
    queryset = OnADateApplication.objects.prefetch_related('user')
    serializer_class = OnADateApplicationSerializer


class PeriodActivityRelatedApplicationsList(TimeBasedActivityRelatedApplicationsList):
    queryset = PeriodApplication.objects.prefetch_related('user')
    serializer_class = PeriodApplicationSerializer


class DateTransitionList(TransitionList):
    serializer_class = DateTransitionSerializer
    queryset = DateActivity.objects.all()


class PeriodTransitionList(TransitionList):
    serializer_class = PeriodTransitionSerializer
    queryset = PeriodActivity.objects.all()


class ApplicationList(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
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

        serializer.save(user=self.request.user)


class OnADateApplicationList(ApplicationList):
    queryset = OnADateApplication.objects.all()
    serializer_class = OnADateApplicationSerializer


class PeriodApplicationList(ApplicationList):
    queryset = PeriodApplication.objects.all()
    serializer_class = PeriodApplicationSerializer


class ApplicationDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributionPermission),
    )


class OnADateApplicationDetail(ApplicationDetail):
    queryset = OnADateApplication.objects.all()
    serializer_class = OnADateApplicationSerializer


class PeriodApplicationDetail(ApplicationDetail):
    queryset = PeriodApplication.objects.all()
    serializer_class = PeriodApplicationSerializer


class ApplicationTransitionList(TransitionList):
    pass


class OnADateApplicationTransitionList(ApplicationTransitionList):
    serializer_class = OnADateApplicationTransitionSerializer
    queryset = OnADateApplication.objects.all()


class PeriodApplicationTransitionList(ApplicationTransitionList):
    serializer_class = PeriodApplicationTransitionSerializer
    queryset = PeriodApplication.objects.all()


class ApplicationDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    queryset = OnADateApplication.objects
    relation = 'document'
    field = 'file'


class OnADateApplicationDocumentDetail(ApplicationDocumentDetail):
    queryset = OnADateApplication.objects


class PeriodApplicationDocumentDetail(ApplicationDocumentDetail):
    queryset = PeriodApplication.objects


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
