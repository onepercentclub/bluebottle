from django.db.models import Sum, Q

from bluebottle.activities.models import Activity
from bluebottle.activities.permissions import (
    IsAdminPermission,
    RelatedActivityOwnerPermission,
)
from bluebottle.bb_accounts.permissions import IsAuthenticatedOrOpenPermission
from bluebottle.members.models import MemberPlatformSettings
from bluebottle.time_based.models import Team
from bluebottle.time_based.models import TeamMember
from bluebottle.time_based.permissions import InviteCodePermission, TeamMemberPermission
from bluebottle.time_based.serializers import TeamSerializer, TeamMemberTransitionSerializer
from bluebottle.time_based.serializers import TeamTransitionSerializer
from bluebottle.time_based.serializers.teams import TeamMemberSerializer
from bluebottle.time_based.views.mixins import (
    CreatePermissionMixin,
    FilterRelatedUserMixin,
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf,
    ResourceOwnerPermission,
    ResourcePermission, )
from bluebottle.utils.views import (
    CreateAPIView,
    JsonApiViewMixin,
    ListAPIView,
    RetrieveUpdateAPIView,
    ExportView,
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
            if self.request.user.is_authenticated:
                queryset = queryset.filter(user=self.request.user)
            else:
                queryset = queryset.none()
        return queryset

    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission),)
    queryset = Team.objects.prefetch_related("activity", "owner", "registration")
    serializer_class = TeamSerializer


class RelatedTeamList(JsonApiViewMixin, ListAPIView, FilterRelatedUserMixin):
    permission_classes = (OneOf(ResourcePermission, ResourceOwnerPermission),)

    def get_queryset(self):
        queryset = super().get_queryset()

        status = self.request.query_params.get("filter[status]")
        if status:
            queryset = queryset.filter(status__in=status.split(","))
            queryset = queryset.order_by('slots__start')

        my = self.request.query_params.get("filter[my]")
        if my:
            if self.request.user.is_authenticated:
                queryset = queryset.filter(team_members__user=self.request.user)
            else:
                queryset = queryset.none()

        sort = self.request.GET.get("sort")
        if sort == "start":
            queryset = queryset.order_by("slots__start")
        if sort == "-start":
            queryset = queryset.order_by("-slots__start")

        return queryset.filter(activity_id=self.kwargs["activity_id"])

    queryset = Team.objects.prefetch_related("activity", "registration")
    serializer_class = TeamSerializer

    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context["display_member_names"] = (
            MemberPlatformSettings.objects.get().display_member_names
        )

        activity = Activity.objects.get(pk=self.kwargs["activity_id"])
        context["owners"] = list(activity.owners)

        if (
            self.request.user
            and self.request.user.is_authenticated
            and (
                self.request.user in context["owners"]
                or self.request.user.is_staff
                or self.request.user.is_superuser
            )
        ):
            context["display_member_names"] = "full_name"

        return context


class RelatedTeamMembers(JsonApiViewMixin, ListAPIView, FilterRelatedUserMixin):
    permission_classes = [IsAuthenticatedOrOpenPermission]

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(**self.kwargs)

    queryset = TeamMember.objects.all()
    serializer_class = TeamMemberSerializer


class TeamDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(
            ResourcePermission,
            ResourceOwnerPermission,
            RelatedActivityOwnerPermission,
            IsAdminPermission,
        ),
    )
    queryset = Team.objects.prefetch_related("activity", "user")
    serializer_class = TeamSerializer


class TeamTransitionList(TransitionList):
    serializer_class = TeamTransitionSerializer
    queryset = Team.objects.all()


class TeamMemberExportView(ExportView):
    filename = "team-members"

    model = Team

    def get_instances(self):
        return self.get_object().team_members.all()

    def get_fields(self):
        fields = (
            ("user__email", "Email"),
            ("user__full_name", "Name"),
            ("created", "Registration Date"),
            ("status", "Status"),
        )
        return fields


class TeamMemberList(JsonApiViewMixin, CreateAPIView, CreatePermissionMixin):

    permission_classes = (InviteCodePermission,)
    queryset = Team.objects.prefetch_related("team", "user", "participants")
    serializer_class = TeamMemberSerializer

    def perform_create(self, serializer):
        if hasattr(serializer.Meta, 'model'):
            self.check_object_permissions(
                self.request,
                serializer.Meta.model(**serializer.validated_data)
            )
        serializer.save(user=self.request.user)


class TeamMemberDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = TeamMember.objects.prefetch_related("team",)
    serializer_class = TeamMemberSerializer
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, TeamMemberPermission),
    )


class TeamMemberTransitionList(TransitionList):
    serializer_class = TeamMemberTransitionSerializer
    queryset = TeamMember.objects.all()
