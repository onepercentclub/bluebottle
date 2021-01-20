from django.db.models import Q
from django.http import HttpResponse
from django.utils.timezone import utc

import icalendar

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ContributorPermission, ContributionPermission, DeleteActivityPermission
)
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant,
    TimeContribution,
    DateActivitySlot, SlotParticipant
)
from bluebottle.time_based.permissions import SlotParticipantPermission
from bluebottle.time_based.serializers import (
    DateActivitySerializer,
    PeriodActivitySerializer,
    DateTransitionSerializer,
    PeriodTransitionSerializer,
    PeriodParticipantSerializer,
    DateParticipantSerializer,
    DateParticipantTransitionSerializer,
    PeriodParticipantTransitionSerializer,
    TimeContributionSerializer,
    DateActivitySlotSerializer,
    SlotParticipantSerializer,
    SlotParticipantTransitionSerializer
)

from bluebottle.transitions.views import TransitionList

from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, RetrieveUpdateDestroyAPIView, ListCreateAPIView,
    CreateAPIView, ListAPIView, JsonApiViewMixin,
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


class DateSlotListView(JsonApiViewMixin, CreateAPIView):
    related_permission_classes = {
        'activity': [ActivityOwnerPermission]
    }
    permission_classes = []
    queryset = DateActivitySlot.objects.all()
    serializer_class = DateActivitySlotSerializer


class DateSlotDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    related_permission_classes = {
        'activity': [ActivityOwnerPermission]
    }
    permission_classes = []
    queryset = DateActivitySlot.objects.all()
    serializer_class = DateActivitySlotSerializer


class TimeBasedActivityRelatedParticipantList(JsonApiViewMixin, ListAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
    pagination_class = None

    def get_queryset(self):
        if self.request.user.is_authenticated():
            queryset = self.queryset.filter(
                Q(user=self.request.user) |
                Q(activity__owner=self.request.user) |
                Q(activity__initiative__activity_manager=self.request.user) |
                Q(status='accepted')
            )
        else:
            queryset = self.queryset.filter(
                status='accepted'
            )

        return queryset.filter(
            activity_id=self.kwargs['activity_id']
        )


class DateActivityRelatedParticipantList(TimeBasedActivityRelatedParticipantList):
    queryset = DateParticipant.objects.prefetch_related('user')
    serializer_class = DateParticipantSerializer


class PeriodActivityRelatedParticipantList(TimeBasedActivityRelatedParticipantList):
    queryset = PeriodParticipant.objects.prefetch_related('user')
    serializer_class = PeriodParticipantSerializer


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


class TimeContributionDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = TimeContribution.objects.all()
    serializer_class = TimeContributionSerializer
    permission_classes = [ContributionPermission]


class ParticipantDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )


class DateParticipantDetail(ParticipantDetail):
    queryset = DateParticipant.objects.all()
    serializer_class = DateParticipantSerializer


class PeriodParticipantDetail(ParticipantDetail):
    queryset = PeriodParticipant.objects.all()
    serializer_class = PeriodParticipantSerializer


class ParticipantTransitionList(TransitionList):
    pass


class DateParticipantTransitionList(ParticipantTransitionList):
    serializer_class = DateParticipantTransitionSerializer
    queryset = DateParticipant.objects.all()


class PeriodParticipantTransitionList(ParticipantTransitionList):
    serializer_class = PeriodParticipantTransitionSerializer
    queryset = PeriodParticipant.objects.all()


class SlotParticipantListView(JsonApiViewMixin, CreateAPIView):
    permission_classes = [SlotParticipantPermission]
    queryset = SlotParticipant.objects.all()
    serializer_class = SlotParticipantSerializer


class SlotParticipantDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = [SlotParticipantPermission]
    queryset = SlotParticipant.objects.all()
    serializer_class = SlotParticipantSerializer


class SlotParticipantTransitionList(TransitionList):
    serializer_class = SlotParticipantTransitionSerializer
    queryset = SlotParticipant.objects.all()


class ParticipantDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    queryset = DateParticipant.objects
    relation = 'document'
    field = 'file'


class DateParticipantDocumentDetail(ParticipantDocumentDetail):
    queryset = DateParticipant.objects


class PeriodParticipantDocumentDetail(ParticipantDocumentDetail):
    queryset = PeriodParticipant.objects


class ActivitySlotIcalView(PrivateFileView):
    queryset = DateActivitySlot.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
        activity__status__in=['cancelled', 'deleted', 'rejected'],
    )

    max_age = 30 * 60  # half an hour

    def get(self, *args, **kwargs):
        instance = self.get_object()
        calendar = icalendar.Calendar()

        slot = icalendar.Event()
        slot.add('summary', instance.activity.title)
        slot.add('description', instance.activity.details)
        slot.add('url', instance.activity.get_absolute_url())
        slot.add('dtstart', instance.start.astimezone(utc))
        slot.add('dtend', (instance.start + instance.duration).astimezone(utc))
        slot['uid'] = instance.uid

        organizer = icalendar.vCalAddress('MAILTO:{}'.format(instance.activity.owner.email))
        organizer.params['cn'] = icalendar.vText(instance.activity.owner.full_name)

        slot['organizer'] = organizer
        if instance.location:
            slot['location'] = icalendar.vText(instance.location.formatted_address)

        calendar.add_component(slot)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.activity.slug
        )

        return response
