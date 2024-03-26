from django.db.models import Sum, Q

from bluebottle.activities.permissions import ContributorPermission
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.time_based.models import DeadlineParticipant, PeriodicParticipant, ScheduleParticipant
from bluebottle.time_based.serializers import (
    DeadlineParticipantSerializer,
    DeadlineParticipantTransitionSerializer, ScheduleParticipantSerializer, ScheduleParticipantTransitionSerializer,
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
    ResourcePermission,
)
from bluebottle.utils.views import (
    CreateAPIView,
    JsonApiViewMixin,
    ListAPIView,
    RetrieveUpdateAPIView,
)


class ParticipantList(JsonApiViewMixin, CreateAPIView, CreatePermissionMixin):

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                total_duration=Sum(
                    "contributions__timecontribution__value",
                    filter=Q(contributions__status__in=["succeeded", "new"]),
                )
            )
        )
        my = self.request.query_params.get("filter[my]")
        if my:
            queryset = queryset.filter(user=self.request.user)
        return queryset

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class DeadlineParticipantList(ParticipantList):
    queryset = DeadlineParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer = DeadlineParticipantSerializer


class ScheduleParticipantList(ParticipantList):
    queryset = ScheduleParticipant.objects.prefetch_related(
        "user",
        "activity",
    )
    serializer = ScheduleParticipantSerializer


class PeriodicParticipantList(ParticipantList):
    queryset = PeriodicParticipant.objects.prefetch_related(
        "user", "activity"
    ).order_by("-slot__start")
    serializer = PeriodicParticipantSerializer


class ParticipantDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )


class DeadlineParticipantDetail(ParticipantDetail):
    queryset = DeadlineParticipant.objects.all()
    serializer_class = DeadlineParticipantSerializer


class ScheduleParticipantDetail(ParticipantDetail):
    queryset = ScheduleParticipant.objects.all()
    serializer_class = ScheduleParticipantSerializer


class PeriodicParticipantDetail(ParticipantDetail):
    queryset = PeriodicParticipant.objects.all()
    serializer_class = PeriodicParticipantSerializer


class RelatedParticipantListView(
    JsonApiViewMixin, ListAPIView, AnonimizeMembersMixin, FilterRelatedUserMixin
):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(activity_id__in=self.kwargs["activity_id"])


class DeadlineRelatedParticipantList(RelatedContributorListView):
    queryset = DeadlineParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineParticipantSerializer


class ScheduleRelatedParticipantList(RelatedContributorListView):
    queryset = ScheduleParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = ScheduleParticipantSerializer


class PeriodicRelatedParticipantList(RelatedContributorListView):
    queryset = PeriodicParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = PeriodicParticipantSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.order_by("-slot__start")
        return queryset


class DeadlineParticipantTransitionList(TransitionList):
    serializer_class = DeadlineParticipantTransitionSerializer
    queryset = DeadlineParticipant.objects.all()


class ScheduleParticipantTransitionList(TransitionList):
    serializer_class = ScheduleParticipantTransitionSerializer
    queryset = ScheduleParticipant.objects.all()


class PeriodicParticipantTransitionList(TransitionList):
    serializer_class = PeriodicParticipantTransitionSerializer
    queryset = PeriodicParticipant.objects.all()
