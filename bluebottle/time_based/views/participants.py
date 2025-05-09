from django.db.models import Q

from bluebottle.activities.permissions import ContributorPermission
from bluebottle.activities.views import ParticipantCreateMixin
from bluebottle.time_based.models import (
    DateActivity,
    DateParticipant,
    DeadlineParticipant,
    PeriodicParticipant,
    ScheduleParticipant,
    TeamScheduleParticipant,
)
from bluebottle.time_based.serializers import (
    DateParticipantSerializer,
    DateParticipantTransitionSerializer,
    DeadlineParticipantSerializer,
    DeadlineParticipantTransitionSerializer,
    ScheduleParticipantSerializer,
    ScheduleParticipantTransitionSerializer,
    TeamScheduleParticipantSerializer,
    TeamScheduleParticipantTransitionSerializer,
)
from bluebottle.time_based.serializers.participants import (
    PeriodicParticipantSerializer,
    PeriodicParticipantTransitionSerializer,
)
from bluebottle.time_based.views.mixins import (
    AnonymizeMembersMixin,
    CreatePermissionMixin,
    FilterRelatedUserMixin,
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    IsAuthenticated,
    IsOwnerOrReadOnly,
    OneOf,
    ResourceOwnerPermission,
    ResourcePermission,
)
from bluebottle.utils.views import (
    CreateAPIView,
    JsonApiPagination,
    JsonApiViewMixin,
    ListAPIView,
    RetrieveUpdateAPIView,
)


class ParticipantList(JsonApiViewMixin, ParticipantCreateMixin, CreateAPIView, CreatePermissionMixin):

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class DateParticipantList(ParticipantList):
    queryset = DateParticipant.objects.prefetch_related(
        'user', 'activity', 'slot'
    )
    serializer_class = DateParticipantSerializer


class DeadlineParticipantList(ParticipantList):
    queryset = DeadlineParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineParticipantSerializer


class ParticipantDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )


class DateParticipantDetail(ParticipantDetail):
    queryset = DateParticipant.objects.all()
    serializer_class = DateParticipantSerializer


class DeadlineParticipantDetail(ParticipantDetail):
    queryset = DeadlineParticipant.objects.all()
    serializer_class = DeadlineParticipantSerializer


class ScheduleParticipantDetail(ParticipantDetail):
    queryset = ScheduleParticipant.objects.all()
    serializer_class = ScheduleParticipantSerializer


class TeamScheduleParticipantDetail(ParticipantDetail):
    queryset = TeamScheduleParticipant.objects.all()
    serializer_class = TeamScheduleParticipantSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)


class PeriodicParticipantDetail(ParticipantDetail):
    queryset = PeriodicParticipant.objects.all()
    serializer_class = PeriodicParticipantSerializer


class RelatedParticipantListView(
    FilterRelatedUserMixin, AnonymizeMembersMixin, JsonApiViewMixin, ListAPIView
):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(activity_id=self.kwargs["activity_id"])


class SlotRelatedParticipantListView(
    AnonymizeMembersMixin, JsonApiViewMixin, ListAPIView,
):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    @property
    def owners(self):
        activity = DateActivity.objects.get(slots=self.kwargs['slot_id'])
        return [activity.owner] + list(activity.owners)

    def get_queryset(self):
        queryset = super().get_queryset().filter(slot_id=self.kwargs['slot_id'])
        activity = DateActivity.objects.get(slots=self.kwargs['slot_id'])
        my = self.request.query_params.get('filter[my]')

        if my:
            if self.request.user.is_authenticated:
                queryset = queryset.filter(user=self.request.user)
            else:
                queryset = queryset.none()

        status_filter = self.request.query_params.get("filter[status]")
        if status_filter:
            statuses = status_filter.split(",")
        else:
            statuses = (
                "accepted",
                "succeeded",
            )
            if (
                self.request.user.is_staff
                or self.request.user.is_superuser
                or self.request.user in activity.owners
            ):
                statuses = (
                    "accepted",
                    "succeeded",
                    "rejected",
                    "withdrawn",
                    "cancelled",
                )

        if self.request.user.is_authenticated and not status_filter:
            if self.request.user.is_staff:
                queryset = queryset
            else:
                queryset = queryset.filter(
                    Q(user=self.request.user) |
                    Q(status__in=statuses)
                ).order_by('-id')
        else:
            queryset = queryset.filter(
                status__in=statuses
            ).order_by('-id')
        return queryset


class DateRelatedParticipantList(RelatedParticipantListView):
    queryset = DateParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DateParticipantSerializer


class DateSlotRelatedParticipantView(SlotRelatedParticipantListView):
    queryset = DateParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DateParticipantSerializer


class MySlotPagination(JsonApiPagination):
    page_size = 3


class DateRegistrationRelatedParticipantView(
    AnonymizeMembersMixin, JsonApiViewMixin, ListAPIView
):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
    pagination_class = MySlotPagination

    queryset = DateParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DateParticipantSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_staff or self.request.user.is_superuser:
                queryset = self.queryset
            else:
                queryset = self.queryset.filter(
                    Q(user=self.request.user) |
                    Q(status__in=('accepted', 'succeeded',))
                ).order_by('-id')
        else:
            queryset = self.queryset.filter(
                status__in=('accepted', 'succeeded',)
            ).order_by('-id')

        status_filter = self.request.query_params.get('filter[status]')
        if status_filter:
            status_values = status_filter.split(',')
            queryset = queryset.filter(status__in=status_values)

        return queryset.filter(registration_id=self.kwargs["registration_id"])


class DeadlineRelatedParticipantList(RelatedParticipantListView):
    queryset = DeadlineParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineParticipantSerializer


class ScheduleRelatedParticipantList(RelatedParticipantListView):
    queryset = ScheduleParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = ScheduleParticipantSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        sort = self.request.GET.get("sort")
        if sort == "start":
            queryset = queryset.order_by("slots__start")
        if sort == "-start":
            queryset = queryset.order_by("-slots__start")

        return queryset


class TeamScheduleRelatedParticipantList(RelatedParticipantListView):
    queryset = TeamScheduleParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = TeamScheduleParticipantSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)


class TeamSlotScheduleRelatedParticipantList(RelatedParticipantListView):
    queryset = TeamScheduleParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = TeamScheduleParticipantSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)


class PeriodicRelatedParticipantList(RelatedParticipantListView):
    queryset = PeriodicParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = PeriodicParticipantSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by("-slot__start")
        return queryset


class DateParticipantTransitionList(TransitionList):
    serializer_class = DateParticipantTransitionSerializer
    queryset = DateParticipant.objects.all()


class DeadlineParticipantTransitionList(TransitionList):
    serializer_class = DeadlineParticipantTransitionSerializer
    queryset = DeadlineParticipant.objects.all()


class ScheduleParticipantTransitionList(TransitionList):
    serializer_class = ScheduleParticipantTransitionSerializer
    queryset = ScheduleParticipant.objects.all()


class TeamScheduleParticipantTransitionList(TransitionList):
    serializer_class = TeamScheduleParticipantTransitionSerializer
    queryset = TeamScheduleParticipant.objects.all()


class PeriodicParticipantTransitionList(TransitionList):
    serializer_class = PeriodicParticipantTransitionSerializer
    queryset = PeriodicParticipant.objects.all()
