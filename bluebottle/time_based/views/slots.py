import dateutil
from datetime import datetime, time

from django.utils.timezone import get_current_timezone

from rest_framework import filters


from bluebottle.activities.permissions import (
    ActivityOwnerPermission,
    ActivityStatusPermission,
    DeleteActivityPermission,
    IsAdminPermission
)
from bluebottle.time_based.models import (
    DateActivitySlot, ScheduleSlot, TeamScheduleSlot,
)
from bluebottle.time_based.serializers import (
    DateActivitySlotSerializer, ScheduleSlotSerializer, TeamScheduleSlotSerializer
)
from bluebottle.time_based.views.mixins import BaseSlotIcalView
from bluebottle.utils.permissions import (
    OneOf,
    ResourcePermission,
    TenantConditionalOpenClose,
)
from bluebottle.utils.views import (
    JsonApiViewMixin,
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)


class DateSlotListView(JsonApiViewMixin, CreateAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission, IsAdminPermission),
        ]
    }

    permission_classes = [TenantConditionalOpenClose]
    queryset = DateActivitySlot.objects.all()
    serializer_class = DateActivitySlotSerializer


class RelatedDateSlotListView(JsonApiViewMixin, ListAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission, IsAdminPermission),
        ]
    }

    permission_classes = [TenantConditionalOpenClose]
    queryset = DateActivitySlot.objects.all()
    serializer_class = DateActivitySlotSerializer
    lookup_field = 'activity_id'
    ordering_fields = ['start']
    filter_backends = [filters.OrderingFilter]

    def get_queryset(self):
        queryset = super().get_queryset()
        tz = get_current_timezone()

        start = self.request.GET.get('start')
        ordering = self.request.GET.get('ordering')
        try:
            if ordering == '-start':
                queryset = queryset.filter(
                    start__lte=dateutil.parser.parse(start).astimezone(tz)
                )
            else:
                queryset = queryset.filter(
                    start__gte=dateutil.parser.parse(start).astimezone(tz)
                )
        except (ValueError, TypeError):
            pass

        end = self.request.GET.get('end')
        try:
            queryset = queryset.filter(
                start__lte=datetime.combine(dateutil.parser.parse(end), time.max).astimezone(tz)
            )
        except (ValueError, TypeError):
            pass

        return queryset


class DateSlotDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission, IsAdminPermission),
            DeleteActivityPermission,
        ]
    }
    permission_classes = [TenantConditionalOpenClose]
    queryset = DateActivitySlot.objects.all()
    serializer_class = DateActivitySlotSerializer


class ScheduleSlotListView(JsonApiViewMixin, CreateAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission, IsAdminPermission),
        ]
    }

    permission_classes = [TenantConditionalOpenClose]
    queryset = ScheduleSlot.objects.all()
    serializer_class = ScheduleSlotSerializer


class ScheduleSlotDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ActivityOwnerPermission, IsAdminPermission),
            DeleteActivityPermission,
        ]
    }
    permission_classes = [TenantConditionalOpenClose]
    queryset = ScheduleSlot.objects.all()
    serializer_class = ScheduleSlotSerializer


class TeamScheduleSlotListView(JsonApiViewMixin, CreateAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ActivityOwnerPermission, IsAdminPermission),
            DeleteActivityPermission,
        ]
    }

    permission_classes = [TenantConditionalOpenClose]
    queryset = TeamScheduleSlot.objects.all()
    serializer_class = TeamScheduleSlotSerializer


class TeamScheduleSlotDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ActivityOwnerPermission, IsAdminPermission),
        ]
    }
    permission_classes = [TenantConditionalOpenClose]
    queryset = TeamScheduleSlot.objects.all()
    serializer_class = TeamScheduleSlotSerializer


class ScheduleSlotSlotIcalView(BaseSlotIcalView):
    queryset = ScheduleSlot.objects.exclude(
        status__in=["cancelled", "deleted", "rejected"],
        activity__status__in=["cancelled", "deleted", "rejected"],
    )


class TeamScheduleSlotSlotIcalView(BaseSlotIcalView):
    queryset = TeamScheduleSlot.objects.exclude(
        status__in=["cancelled", "deleted", "rejected"],
        activity__status__in=["cancelled", "deleted", "rejected"],
    )
