from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ActivitySegmentPermission
)
from bluebottle.activities.views import ActivityDetailView
from bluebottle.funding.views import PayoutDetails
from bluebottle.grant_management.models import (
    GrantApplication, GrantPayout
)
from bluebottle.grant_management.serializers import (
    GrantApplicationSerializer, GrantApplicationTransitionSerializer, GrantPayoutSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import OneOf, ResourcePermission
from bluebottle.utils.views import (
    ListCreateAPIView, JsonApiViewMixin
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
        serializer.validated_data['owner'] = self.request.user
        super().perform_create(serializer)


class GrantApplicationDetail(ActivityDetailView):
    queryset = GrantApplication.objects.all()

    serializer_class = GrantApplicationSerializer
    permission_classes = (
        ActivityStatusPermission,
        ActivitySegmentPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )


class GrantPayoutDetails(PayoutDetails):
    queryset = GrantPayout.objects.all()
    serializer_class = GrantPayoutSerializer


class GrantApplicationTransitionList(TransitionList):
    serializer_class = GrantApplicationTransitionSerializer
    queryset = GrantApplication.objects.all()

    prefetch_for_includes = {
        'resource': ['grant_application'],
    }
