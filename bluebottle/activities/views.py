from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import ListAPIView, JsonApiViewMixin, RetrieveUpdateDestroyAPIView


class ActivityList(JsonApiViewMixin, ListAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    model = Activity

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    prefetch_for_includes = {
        'owner': ['owner'],
        'initiative': ['initiative'],
    }


class ActivityDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    model = Activity
    lookup_field = 'pk'

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    prefetch_for_includes = {
        'owner': ['owner'],
        'initiative': ['initiative'],
    }
