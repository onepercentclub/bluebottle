from rest_framework.pagination import PageNumberPagination

from bluebottle.segments.permissions import OpenSegmentOrMember
from bluebottle.utils.views import ListAPIView, RetrieveAPIView, JsonApiViewMixin
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.segments.serializers import (
    SegmentSerializer, SegmentTypeSerializer, SegmentPublicDetailSerializer
)

from bluebottle.utils.permissions import TenantConditionalOpenClose


class SegmentPagination(PageNumberPagination):
    page_size = 100


class SegmentTypeList(JsonApiViewMixin, ListAPIView):
    serializer_class = SegmentTypeSerializer
    queryset = SegmentType.objects.filter(is_active=True).prefetch_related('segments')
    permission_classes = [TenantConditionalOpenClose, ]


class SegmentList(JsonApiViewMixin, ListAPIView):
    serializer_class = SegmentSerializer
    queryset = Segment.objects.filter(segment_type__is_active=True).select_related('segment_type')

    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = SegmentPagination


class SegmentDetail(JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SegmentSerializer
    queryset = Segment.objects.filter(segment_type__is_active=True).select_related('segment_type')

    permission_classes = [
        OpenSegmentOrMember,
        TenantConditionalOpenClose,
    ]


class SegmentPublicDetail(JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SegmentPublicDetailSerializer
    queryset = Segment.objects.filter(segment_type__is_active=True).select_related('segment_type')

    permission_classes = [
        OpenSegmentOrMember,
    ]
