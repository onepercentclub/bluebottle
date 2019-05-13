from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import ListAPIView, JsonApiViewMixin


class ActivityList(JsonApiViewMixin, ListAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    prefetch_for_includes = {
        'owner': ['owner'],
        'initiatives': ['initiatives'],
    }
