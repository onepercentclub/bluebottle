from bluebottle.activities.models import Activity
from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    DeleteActivityPermission, ActivitySegmentPermission
)
from bluebottle.segments.views import ClosedSegmentActivityViewMixin
from bluebottle.time_based.models import DateActivity, DeadlineActivity, PeriodicActivity, ScheduleActivity, \
    RegisteredDateActivity
from bluebottle.time_based.serializers import (
    DateActivitySerializer, DeadlineActivitySerializer,
    DateTransitionSerializer, DeadlineTransitionSerializer,
    PeriodicActivitySerializer, PeriodicTransitionSerializer, PeriodActivitySerializer, ScheduleActivitySerializer,
    ScheduleTransitionSerializer, RegisteredDateActivitySerializer, RegisteredDateTransitionSerializer
)
from bluebottle.time_based.views.mixins import CreatePermissionMixin
from bluebottle.transitions.views import TransitionList
from bluebottle.updates.permissions import IsStaffMember
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission
)
from bluebottle.utils.views import (
    RetrieveUpdateDestroyAPIView, ListCreateAPIView, JsonApiViewMixin,
)


class TimeBasedActivityListView(JsonApiViewMixin, ListCreateAPIView, CreatePermissionMixin):
    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission, IsStaffMember),
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


class RegisteredDateActivityListView(TimeBasedActivityListView):
    queryset = RegisteredDateActivity.objects.all()
    serializer_class = RegisteredDateActivitySerializer


class ScheduleActivityListView(TimeBasedActivityListView):
    queryset = ScheduleActivity.objects.all()
    serializer_class = ScheduleActivitySerializer


class PeriodicActivityListView(TimeBasedActivityListView):
    queryset = PeriodicActivity.objects.all()
    serializer_class = PeriodicActivitySerializer


class DateActivityDetailView(TimeBasedActivityDetailView):
    queryset = DateActivity.objects.all()
    serializer_class = DateActivitySerializer


class PeriodActivityDetailView(TimeBasedActivityDetailView):
    queryset = Activity.objects.all()
    serializer_class = PeriodActivitySerializer


class DeadlineActivityDetailView(TimeBasedActivityDetailView):
    queryset = DeadlineActivity.objects.all()
    serializer_class = DeadlineActivitySerializer


class RegisteredDateActivityDetailView(TimeBasedActivityDetailView):
    queryset = RegisteredDateActivity.objects.all()
    serializer_class = RegisteredDateActivitySerializer


class ScheduleActivityDetailView(TimeBasedActivityDetailView):
    queryset = ScheduleActivity.objects.all()
    serializer_class = ScheduleActivitySerializer


class PeriodicActivityDetailView(TimeBasedActivityDetailView):
    queryset = PeriodicActivity.objects.all()
    serializer_class = PeriodicActivitySerializer


class DateTransitionList(TransitionList):
    serializer_class = DateTransitionSerializer
    queryset = DateActivity.objects.all()


class DeadlineTransitionList(TransitionList):
    serializer_class = DeadlineTransitionSerializer
    queryset = DeadlineActivity.objects.all()


class RegisteredDateTransitionList(TransitionList):
    serializer_class = RegisteredDateTransitionSerializer
    queryset = RegisteredDateActivity.objects.all()


class ScheduleTransitionList(TransitionList):
    serializer_class = ScheduleTransitionSerializer
    queryset = ScheduleActivity.objects.all()


class PeriodicTransitionList(TransitionList):
    serializer_class = PeriodicTransitionSerializer
    queryset = PeriodicActivity.objects.all()
