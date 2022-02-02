from rest_framework.pagination import PageNumberPagination

from bluebottle.utils.views import ListAPIView, RetrieveAPIView, JsonApiViewMixin
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.segments.serializers import (
    SegmentListSerializer, SegmentDetailSerializer, SegmentTypeSerializer
)

from bluebottle.utils.permissions import TenantConditionalOpenClose


class SegmentPagination(PageNumberPagination):
    page_size = 100


class SegmentTypeList(JsonApiViewMixin, ListAPIView):
    serializer_class = SegmentTypeSerializer
    queryset = SegmentType.objects.filter(is_active=True).prefetch_related('segments')
    permission_classes = [TenantConditionalOpenClose, ]


class SegmentList(JsonApiViewMixin, ListAPIView):
    serializer_class = SegmentListSerializer
    queryset = Segment.objects.filter(segment_type__is_active=True).select_related('segment_type')

    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = SegmentPagination


class SegmentDetail(JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SegmentDetailSerializer
    queryset = Segment.objects.filter(segment_type__is_active=True).select_related('segment_type')

    permission_classes = [TenantConditionalOpenClose, ]
