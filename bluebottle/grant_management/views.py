from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ActivitySegmentPermission
)
from bluebottle.funding.views import PayoutDetails
from bluebottle.grant_management.models import (
    GrantApplication, GrantPayout
)
from bluebottle.grant_management.serializers import (
    GrantApplicationSerializer, GrantApplicationTransitionSerializer, GrantPayoutSerializer
)
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import OneOf, ResourcePermission
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin
)


class GrantApplicationList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = GrantApplication.objects.all()
    serializer_class = GrantApplicationSerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'owner': ['owner'],
    }

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


class GrantApplicationDetail(
    JsonApiViewMixin, ClosedSegmentActivityViewMixin,
    AutoPrefetchMixin, RetrieveUpdateAPIView
):
    queryset = GrantApplication.objects.select_related(
        'initiative', 'initiative__owner',
    )

    serializer_class = GrantApplicationSerializer
    permission_classes = (
        ActivityStatusPermission,
        ActivitySegmentPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    prefetch_for_includes = {
        'initiative': ['initiative'],
        'owner': ['owner'],
    }


class GrantPayoutDetails(PayoutDetails):
    queryset = GrantPayout.objects.all()
    serializer_class = GrantPayoutSerializer


class GrantApplicationTransitionList(TransitionList):
    serializer_class = GrantApplicationTransitionSerializer
    queryset = GrantApplication.objects.all()

    prefetch_for_includes = {
        'resource': ['grant_application'],
    }
