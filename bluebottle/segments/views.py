from rest_framework.pagination import PageNumberPagination

from bluebottle.segments.models import Segment, SegmentType
from bluebottle.segments.permissions import OpenSegmentOrMember
from bluebottle.segments.serializers import (
    SegmentDetailSerializer, SegmentPublicDetailSerializer, SegmentListSerializer, SegmentTypeSerializer
)
from bluebottle.utils.permissions import TenantConditionalOpenClose
from bluebottle.utils.views import ListAPIView, RetrieveAPIView, JsonApiViewMixin
from rest_framework import exceptions


class ClosedSegmentActivityViewMixin(object):
    def permission_denied(self, request, message=None, code=None):
        if request.authenticators and not request.successful_authenticator:
            if code and message:
                raise exceptions.NotAuthenticated(detail=message, code=code)
        raise exceptions.PermissionDenied(detail=message, code=code)


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

    permission_classes = [
        OpenSegmentOrMember,
        TenantConditionalOpenClose,
    ]


class SegmentPublicDetail(JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SegmentPublicDetailSerializer
    queryset = Segment.objects.filter(segment_type__is_active=True).select_related('segment_type')

    permission_classes = [
        TenantConditionalOpenClose,
    ]
