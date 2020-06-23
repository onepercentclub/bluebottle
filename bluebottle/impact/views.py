from rest_framework import filters

from bluebottle.activities.permissions import ActivityOwnerPermission
from bluebottle.impact.models import ImpactType, ImpactGoal
from bluebottle.impact.serializers import ImpactTypeSerializer, ImpactGoalSerializer
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission
)
from bluebottle.utils.views import (
    JsonApiViewMixin,
    ListAPIView,
    CreateAPIView,
    RetrieveUpdateAPIView
)


class ImpactTypeSearchFilter(filters.SearchFilter):
    search_param = "filter[search]"


class ImpactTypeList(JsonApiViewMixin, ListAPIView):
    queryset = ImpactType.objects.filter(active=True)

    permission_classes = []
    serializer_class = ImpactTypeSerializer
    filter_backends = (ImpactTypeSearchFilter, )


class ImpactGoalList(JsonApiViewMixin, CreateAPIView):
    queryset = ImpactGoal.objects.filter()

    related_permission_classes = {
        'content_object': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }
    permission_classes = []

    serializer_class = ImpactGoalSerializer


class ImpactGoalDetail(JsonApiViewMixin, RetrieveUpdateAPIView):
    queryset = ImpactGoal.objects.filter()

    related_permission_classes = {
        'content_object': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }
    permission_classes = []

    serializer_class = ImpactGoalSerializer
