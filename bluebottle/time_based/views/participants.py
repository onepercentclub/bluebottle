from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

from bluebottle.activities.permissions import ContributorPermission
from bluebottle.activities.views import RelatedContributorListView
from bluebottle.members.models import Member
from bluebottle.time_based.models import DeadlineParticipant, PeriodicParticipant, ScheduleParticipant, \
    TeamScheduleParticipant
from bluebottle.time_based.serializers import (
    DeadlineParticipantSerializer,
    DeadlineParticipantTransitionSerializer,
    ScheduleParticipantSerializer, ScheduleParticipantTransitionSerializer,
    TeamScheduleParticipantSerializer, TeamScheduleParticipantTransitionSerializer
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


class ParticipantList(JsonApiViewMixin, CreateAPIView, CreatePermissionMixin):

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def perform_create(self, serializer):
        email = serializer.validated_data.pop('email', None)
        send_messages = serializer.validated_data.pop('send_messages', True)
        if email:
            user = Member.objects.filter(email__iexact=email).first()
            if not user:
                raise ValidationError(_('User with email address not found'))
        else:
            user = self.request.user

        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        if not email:
            if self.request.user.required:
                raise ValidationError('Required fields', code="required")

        activity = serializer.validated_data['activity']
        if self.queryset.filter(user=user, activity=activity).exists():
            raise ValidationError(_('User already joined'), code="exists")

        serializer.save(user=user, send_messages=send_messages)


class DeadlineParticipantList(ParticipantList):
    queryset = DeadlineParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineParticipantSerializer


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


class TeamScheduleParticipantDetail(ParticipantDetail):
    queryset = TeamScheduleParticipant.objects.all()
    serializer_class = TeamScheduleParticipantSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)


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

    def get_queryset(self):
        queryset = super().get_queryset()

        sort = self.request.GET.get("sort")
        if sort == "start":
            queryset = queryset.order_by("slots__start")
        if sort == "-start":
            queryset = queryset.order_by("-slots__start")

        return queryset


class TeamScheduleRelatedParticipantList(RelatedContributorListView):
    queryset = TeamScheduleParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = TeamScheduleParticipantSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)


class TeamSlotScheduleRelatedParticipantList(RelatedContributorListView):
    queryset = TeamScheduleParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = TeamScheduleParticipantSerializer
    permission_classes = (IsAuthenticated, IsOwnerOrReadOnly)


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


class TeamScheduleParticipantTransitionList(TransitionList):
    serializer_class = TeamScheduleParticipantTransitionSerializer
    queryset = TeamScheduleParticipant.objects.all()


class PeriodicParticipantTransitionList(TransitionList):
    serializer_class = PeriodicParticipantTransitionSerializer
    queryset = PeriodicParticipant.objects.all()
