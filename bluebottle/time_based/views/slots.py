from bluebottle.activities.permissions import (
    ActivityOwnerPermission,
    ActivityStatusPermission,
    DeleteActivityPermission,
)
from bluebottle.time_based.models import (
    ScheduleSlot,
)
from bluebottle.time_based.serializers import (
    ScheduleSlotSerializer,
)
from bluebottle.utils.permissions import (
    OneOf,
    ResourcePermission,
    TenantConditionalOpenClose,
)
from bluebottle.utils.views import (
    JsonApiViewMixin,
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
)


class ScheduleSlotListView(JsonApiViewMixin, CreateAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission),
            DeleteActivityPermission,
        ]
    }

    permission_classes = [TenantConditionalOpenClose]
    queryset = ScheduleSlot.objects.all()
    serializer_class = ScheduleSlotSerializer


class ScheduleSlotDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    related_permission_classes = {
        "activity": [
            ActivityStatusPermission,
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }
    queryset = ScheduleSlot.objects.all()
    serializer_class = ScheduleSlotSerializer
