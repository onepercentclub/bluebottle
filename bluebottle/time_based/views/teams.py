from django.db.models import Sum, Q

from bluebottle.activities.permissions import ContributorPermission

from bluebottle.activities.views import RelatedContributorListView
from bluebottle.time_based.serializers import TeamSerializer
from bluebottle.time_based.models import (
    Team,
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
    IsAuthenticated,
    IsOwnerOrReadOnly,
)
from bluebottle.utils.views import (
    CreateAPIView,
    JsonApiViewMixin,
    ListAPIView,
    RetrieveUpdateAPIView,
)


class TeamList(JsonApiViewMixin, CreateAPIView, CreatePermissionMixin):

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

    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission),)
    queryset = Team.objects.prefetch_related("activity", "owner", "registration")
    serializer_class = TeamSerializer


class RelatedTeamList(
    JsonApiViewMixin, ListAPIView, AnonimizeMembersMixin, FilterRelatedUserMixin
):
    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission),)

    def get_queryset(self):
        queryset = super().get_queryset()

        status = self.request.query_params.get("filter[status]")
        if status:
            queryset = queryset.filter(status__in=status.split(","))

        return queryset.filter(activity_id__in=self.kwargs["activity_id"])

    queryset = Team.objects.prefetch_related("activity", "owner", "registration")
    serializer_class = TeamSerializer


class TeamDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )
    queryset = Team.objects.prefetch_related("activity", "owner", "registration")
    serializer_class = TeamSerializer


class TeamTransitionList(TransitionList):
    serializer_class = TeamSerializer
    queryset = Team.objects.all()
