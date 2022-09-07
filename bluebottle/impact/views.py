from rest_framework import filters
from rest_framework.pagination import PageNumberPagination

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
    RetrieveUpdateDestroyAPIView, RetrieveAPIView
)
from bluebottle.utils.permissions import TenantConditionalOpenClose


class ImpactTypeSearchFilter(filters.SearchFilter):
    search_param = "filter[search]"


class ImpactTypePagination(PageNumberPagination):
    page_size = 100


class ImpactTypeList(JsonApiViewMixin, ListAPIView):
    queryset = ImpactType.objects.filter(active=True)

    permission_classes = [TenantConditionalOpenClose, ]
    serializer_class = ImpactTypeSerializer
    pagination_class = ImpactTypePagination
    filter_backends = (ImpactTypeSearchFilter, )


class ImpactTypeDetail(JsonApiViewMixin, RetrieveAPIView):
    queryset = ImpactType.objects.filter(active=True)

    permission_classes = [TenantConditionalOpenClose, ]
    serializer_class = ImpactTypeSerializer
    pagination_class = ImpactTypePagination
    filter_backends = (ImpactTypeSearchFilter, )


class ImpactGoalList(JsonApiViewMixin, CreateAPIView):
    queryset = ImpactGoal.objects.filter()

    related_permission_classes = {
        'activity': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }
    permission_classes = []

    serializer_class = ImpactGoalSerializer


class ImpactGoalDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = ImpactGoal.objects.filter()

    related_permission_classes = {
        'activity': [
            OneOf(ResourcePermission, ActivityOwnerPermission),
        ]
    }
    permission_classes = []

    serializer_class = ImpactGoalSerializer
