from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission
)
from bluebottle.time_based.models import OnADateActivity, WithADeadlineActivity, OngoingActivity
from bluebottle.time_based.serializers import (
    OnADateActivitySerializer,
    WithADeadlineActivitySerializer,
    OngoingActivitySerializer
)
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, ListCreateAPIView, JsonApiViewMixin
)


class TimeBasedActivityListView(JsonApiViewMixin, ListCreateAPIView):
    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

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


class TimeBasedActivityDetailView(JsonApiViewMixin, RetrieveUpdateAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )


class OnADateActivityListView(TimeBasedActivityListView):
    queryset = OnADateActivity.objects.all()
    serializer_class = OnADateActivitySerializer


class WithADeadlineActivityListView(TimeBasedActivityListView):
    queryset = WithADeadlineActivity.objects.all()
    serializer_class = WithADeadlineActivitySerializer


class OngoingActivityListView(TimeBasedActivityListView):
    queryset = OngoingActivity.objects.all()
    serializer_class = OngoingActivitySerializer


class OnADateActivityDetailView(TimeBasedActivityDetailView):
    queryset = OnADateActivity.objects.all()
    serializer_class = OnADateActivitySerializer


class WithADeadlineActivityDetailView(TimeBasedActivityDetailView):
    queryset = WithADeadlineActivity.objects.all()
    serializer_class = WithADeadlineActivitySerializer


class OngoingActivityDetailView(TimeBasedActivityDetailView):
    queryset = OngoingActivity.objects.all()
    serializer_class = OngoingActivitySerializer
