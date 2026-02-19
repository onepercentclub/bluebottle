from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    DeleteActivityPermission, ContributorPermission, ActivitySegmentPermission, ActivityManagerPermission
)
from bluebottle.activities.views import RelatedContributorListView, ParticipantCreateMixin
from bluebottle.deeds.models import Deed, DeedParticipant
from bluebottle.deeds.serializers import (
    DeedSerializer, DeedTransitionSerializer, DeedParticipantSerializer,
    DeedParticipantTransitionSerializer
)
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.transitions.views import TransitionList
from bluebottle.updates.permissions import IsStaffMember
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import (
    RetrieveUpdateDestroyAPIView, ListCreateAPIView, RetrieveUpdateAPIView,
    JsonApiViewMixin, ExportView, IcalView
)


class DeedListView(JsonApiViewMixin, ListCreateAPIView):
    queryset = Deed.objects.all()
    serializer_class = DeedSerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission, IsStaffMember),
    )

    def perform_create(self, serializer):
        serializer.validated_data['owner'] = self.request.user
        super().perform_create(serializer)


class DeedDetailView(JsonApiViewMixin, ClosedSegmentActivityViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
        ActivitySegmentPermission,
        DeleteActivityPermission
    )

    queryset = Deed.objects.all()
    serializer_class = DeedSerializer


class DeedTransitionList(TransitionList):
    serializer_class = DeedTransitionSerializer
    queryset = Deed.objects.all()


class DeedRelatedParticipantList(RelatedContributorListView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    queryset = DeedParticipant.objects.prefetch_related('user')
    serializer_class = DeedParticipantSerializer


class ParticipantList(JsonApiViewMixin, ParticipantCreateMixin, ListCreateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ActivityManagerPermission),
    )
    queryset = DeedParticipant.objects.all()
    serializer_class = DeedParticipantSerializer


class ParticipantDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributorPermission),
    )
    queryset = DeedParticipant.objects.all()
    serializer_class = DeedParticipantSerializer


class ParticipantTransitionList(TransitionList):
    serializer_class = DeedParticipantTransitionSerializer
    queryset = DeedParticipant.objects.all()


class ParticipantExportView(ExportView):
    fields = (
        ('user__email', 'Email'),
        ('user__full_name', 'Name'),
        ('created', 'Registration Date'),
        ('status', 'Status'),
    )

    model = Deed
    filename = 'participants'

    def get_instances(self):
        return self.get_object().contributors.instance_of(
            DeedParticipant
        )


class DeedIcalView(IcalView):
    queryset = Deed.objects.exclude(
        status__in=['cancelled', 'deleted', 'rejected'],
    )
