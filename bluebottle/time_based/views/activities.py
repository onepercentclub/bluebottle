from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    DeleteActivityPermission, ActivitySegmentPermission
)
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.time_based.models import DateActivity, DeadlineActivity, PeriodicActivity
from bluebottle.time_based.serializers import (
    DateActivitySerializer, DeadlineActivitySerializer,
    DateTransitionSerializer, DeadlineTransitionSerializer,
    PeriodicActivitySerializer, PeriodicTransitionSerializer
)
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission
)
from bluebottle.utils.views import (
    RetrieveUpdateDestroyAPIView, ListCreateAPIView, JsonApiViewMixin,
)
from bluebottle.time_based.views.mixins import CreatePermissionMixin
from bluebottle.transitions.views import TransitionList


class TimeBasedActivityListView(JsonApiViewMixin, ListCreateAPIView, CreatePermissionMixin):
    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )


class TimeBasedActivityDetailView(JsonApiViewMixin, ClosedSegmentActivityViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
        DeleteActivityPermission,
        ActivitySegmentPermission,
    )


class DateActivityListView(TimeBasedActivityListView):
    queryset = DateActivity.objects.all()
    serializer_class = DateActivitySerializer


class DeadlineActivityListView(TimeBasedActivityListView):
    queryset = DeadlineActivity.objects.all()
    serializer_class = DeadlineActivitySerializer


class PeriodicActivityListView(TimeBasedActivityListView):
    queryset = PeriodicActivity.objects.all()
    serializer_class = PeriodicActivitySerializer


class DateActivityDetailView(TimeBasedActivityDetailView):
    queryset = DateActivity.objects.all()
    serializer_class = DateActivitySerializer


class DeadlineActivityDetailView(TimeBasedActivityDetailView):
    queryset = DeadlineActivity.objects.all()
    serializer_class = DeadlineActivitySerializer


class PeriodicActivityDetailView(TimeBasedActivityDetailView):
    queryset = PeriodicActivity.objects.all()
    serializer_class = PeriodicActivitySerializer


class DateTransitionList(TransitionList):
    serializer_class = DateTransitionSerializer
    queryset = DateActivity.objects.all()


class DeadlineTransitionList(TransitionList):
    serializer_class = DeadlineTransitionSerializer
    queryset = DeadlineActivity.objects.all()


class PeriodicTransitionList(TransitionList):
    serializer_class = PeriodicTransitionSerializer
    queryset = PeriodicActivity.objects.all()
