from bluebottle.utils.views import ListAPIView
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)

from bluebottle.activities.models import Activity
from bluebottle.activities.serializers import ActivitySerializer
from bluebottle.bluebottle_drf2.pagination import BluebottlePagination


class ActivityPagination(BluebottlePagination):
    page_size_query_param = 'page_size'
    page_size = 8


class ActivityList(ListAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    pagination_class = ActivityPagination

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
