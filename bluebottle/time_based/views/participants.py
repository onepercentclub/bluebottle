from rest_framework import filters

from bluebottle.activities.views import RelatedContributorListView
from bluebottle.activities.permissions import ContributorPermission

from bluebottle.time_based.models import DeadlineParticipant, PeriodicParticipant
from bluebottle.time_based.serializers import (
    DeadlineParticipantSerializer, DeadlineParticipantTransitionSerializer
)
from bluebottle.time_based.serializers.participants import PeriodicParticipantSerializer, PeriodicParticipantTransitionSerializer
from bluebottle.time_based.views.mixins import (
    CreatePermissionMixin, AnonimizeMembersMixin, FilterRelatedUserMixin
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf,
    ResourceOwnerPermission,
    ResourcePermission,
)
from bluebottle.utils.views import (
    JsonApiViewMixin, ListAPIView, CreateAPIView, RetrieveUpdateAPIView
)


class ParticipantList(JsonApiViewMixin, CreateAPIView, CreatePermissionMixin):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class DeadlineParticipantList(ParticipantList):
    queryset = DeadlineParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer = DeadlineParticipantSerializer


class PeriodicParticipantList(ParticipantList):
    queryset = PeriodicParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer = PeriodicParticipantSerializer


class ParticipantDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )

class DeadlineParticipantDetail(ParticipantDetail):
    queryset = DeadlineParticipant.objects.all()
    serializer_class = DeadlineParticipantSerializer


class PeriodicParticipantDetail(ParticipantDetail):
    queryset = PeriodicParticipant.objects.all()
    serializer_class = PeriodicParticipantSerializer


class RelatedParticipantListView(
    JsonApiViewMixin, ListAPIView, AnonimizeMembersMixin, FilterRelatedUserMixin
):
    search_fields = ['user__first_name', 'user__last_name']
    filter_backends = [filters.SearchFilter]

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def get_queryset(self):
        queryset = super().get_queryset()

        return queryset.filter(
            activity_id=self.kwargs['activity_id']
        )


class DeadlineRelatedParticipantList(RelatedContributorListView):
    queryset = DeadlineParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = DeadlineParticipantSerializer


class PeriodicRelatedParticipantList(RelatedContributorListView):
    queryset = PeriodicParticipant.objects.prefetch_related(
        'user', 'activity'
    )
    serializer_class = PeriodicParticipantSerializer


class DeadlineParticipantTransitionList(TransitionList):
    serializer_class = DeadlineParticipantTransitionSerializer
    queryset = DeadlineParticipant.objects.all()


class PeriodicParticipantTransitionList(TransitionList):
    serializer_class = PeriodicParticipantTransitionSerializer
    queryset = PeriodicParticipant.objects.all()
