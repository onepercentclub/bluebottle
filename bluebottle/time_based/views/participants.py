from django.db.models import Q

from bluebottle.activities.permissions import ContributorPermission
from bluebottle.activities.views import ParticipantCreateMixin
from bluebottle.time_based.models import DeadlineParticipant, PeriodicParticipant, ScheduleParticipant, \
    TeamScheduleParticipant, DateParticipant, DateActivity
from bluebottle.time_based.serializers import (
    DeadlineParticipantSerializer,
    DeadlineParticipantTransitionSerializer,
    DateParticipantTransitionSerializer,
    ScheduleParticipantSerializer, ScheduleParticipantTransitionSerializer,
    TeamScheduleParticipantSerializer, TeamScheduleParticipantTransitionSerializer, DateParticipantSerializer
)
from bluebottle.time_based.serializers.participants import (
    PeriodicParticipantSerializer,
    PeriodicParticipantTransitionSerializer,
)
from bluebottle.time_based.views.mixins import (
    AnonimizeMembersMixin,
    CreatePermissionMixin,
    FilterRelatedUserMixin,
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf,
    ResourceOwnerPermission,
    ResourcePermission, IsAuthenticated, IsOwnerOrReadOnly,
)
from bluebottle.utils.views import (
    CreateAPIView,
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
        'user', 'activity'
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
    FilterRelatedUserMixin, AnonimizeMembersMixin, JsonApiViewMixin, ListAPIView
):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(activity_id=self.kwargs["activity_id"])


class SlotRelatedParticipantListView(
    AnonimizeMembersMixin, JsonApiViewMixin, ListAPIView, 
):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    @property
    def owners(self):
        activity = DateActivity.objects.get(slots=self.kwargs['slot_id'])
        return [activity.owner] + list(activity.initiative.activity_managers.all())

    def get_queryset(self):
        queryset = super().get_queryset().filter(slot_id=self.kwargs['slot_id'])

        if self.request.user.is_authenticated:
            if self.request.user.is_staff:
                queryset = self.queryset
            else:
                queryset = self.queryset.filter(
                    Q(user=self.request.user) |
                    Q(slot__activity__owner=self.request.user) |
                    Q(slot__activity__initiative__activity_manager=self.request.user) |
                    Q(status__in=('accepted', 'succeeded',))
                ).order_by('-id')
        else:
            queryset = self.queryset.filter(
                status__in=('accepted', 'succeeded',)
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
