from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    ContributionPermission
)
from bluebottle.time_based.models import (
    OnADateActivity, WithADeadlineActivity, OngoingActivity,
    OnADateApplication
)
from bluebottle.time_based.serializers import (
    OnADateActivitySerializer,
    WithADeadlineActivitySerializer,
    OngoingActivitySerializer,
    OnADateTransitionSerializer,
    WithADeadlineTransitionSerializer,
    OngoingTransitionSerializer,
    ApplicationSerializer,
    ApplicationTransitionSerializer
)

from bluebottle.transitions.views import TransitionList

from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, ListCreateAPIView, JsonApiViewMixin,
    PrivateFileView
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


class OnADateTransitionList(TransitionList):
    serializer_class = OnADateTransitionSerializer
    queryset = OnADateActivity.objects.all()


class WithADeadlineTransitionList(TransitionList):
    serializer_class = WithADeadlineTransitionSerializer
    queryset = WithADeadlineActivity.objects.all()


class OngoingTransitionList(TransitionList):
    serializer_class = OngoingTransitionSerializer
    queryset = OngoingActivity.objects.all()


class ApplicationList(JsonApiViewMixin, ListCreateAPIView):
    queryset = OnADateApplication.objects.all()
    serializer_class = ApplicationSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    prefetch_for_includes = {
        'assignment': ['assignment'],
        'user': ['user'],
        'document': ['document'],
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

        serializer.save(user=self.request.user)


class ApplicationDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = OnADateApplication.objects.all()
    serializer_class = ApplicationSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission, ContributionPermission),
    )

    prefetch_for_includes = {
        'activity': ['activity'],
        'user': ['user'],
        'document': ['document'],
    }


class ApplicationTransitionList(TransitionList):
    serializer_class = ApplicationTransitionSerializer
    queryset = OnADateApplication.objects.all()
    prefetch_for_includes = {
        'resource': ['participant', 'participant__activity'],
    }


class ApplicationDocumentDetail(PrivateFileView):
    max_age = 15 * 60  # 15 minutes
    queryset = OnADateApplication.objects
    relation = 'document'
    field = 'file'
