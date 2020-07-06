from rest_framework.pagination import PageNumberPagination

from bluebottle.utils.views import ListAPIView, JsonApiViewMixin
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.segments.serializers import SegmentSerializer, SegmentTypeSerializer

from bluebottle.utils.permissions import TenantConditionalOpenClose


class SegmentPagination(PageNumberPagination):
    page_size = 100


class SegmentTypeList(JsonApiViewMixin, ListAPIView):
    serializer_class = SegmentTypeSerializer
    queryset = SegmentType.objects.filter(is_active=True).prefetch_related('segments')
    permission_classes = [TenantConditionalOpenClose, ]


class SegmentList(JsonApiViewMixin, ListAPIView):
    serializer_class = SegmentSerializer
    queryset = Segment.objects.filter(type__is_active=True).select_related('type')

    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = SegmentPagination
