from django.db.models import Q

from rest_framework.pagination import PageNumberPagination

from bluebottle.activities.permissions import ActivitySegmentPermission
from bluebottle.segments.models import Segment, SegmentType
from bluebottle.segments.permissions import OpenSegmentOrMember
from bluebottle.segments.serializers import (
    SegmentDetailSerializer, SegmentPublicDetailSerializer, SegmentListSerializer, SegmentTypeSerializer
)
from bluebottle.utils.permissions import TenantConditionalOpenClose
from bluebottle.utils.views import ListAPIView, RetrieveAPIView, JsonApiViewMixin
from rest_framework import exceptions


class ClosedSegmentActivityViewMixin(object):

    def check_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                if isinstance(permission, ActivitySegmentPermission):
                    code = 'closed_segment'
                    message = obj.segments.filter(closed=True).first().id
                    if request.authenticators and not request.successful_authenticator:
                        raise exceptions.NotAuthenticated(detail=message, code=code)
                    raise exceptions.PermissionDenied(detail=message, code=code)
                else:
                    self.permission_denied(
                        request,
                        message=getattr(permission, 'message', None),
                        code=getattr(permission, 'code', None)
                    )


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


class RelatedSegmentDetail(JsonApiViewMixin, ListAPIView):
    serializer_class = SegmentDetailSerializer
    queryset = Segment.objects.filter(segment_type__is_active=True).select_related('segment_type')

    pagination_class = None

    permission_classes = [
        OpenSegmentOrMember,
        TenantConditionalOpenClose,
    ]

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            segment_type_id=self.kwargs['segment_type'],
        )

        if not self.request.user.is_staff:
            if self.request.user.is_authenticated:
                user_segments = (segment.pk for segment in self.request.user.segments.all())
            else:
                user_segments = []

            queryset = queryset.filter(
                Q(closed=False) | Q(pk__in=user_segments)
            )

        return queryset


class SegmentPublicDetail(JsonApiViewMixin, RetrieveAPIView):
    serializer_class = SegmentPublicDetailSerializer
    queryset = Segment.objects.filter(segment_type__is_active=True).select_related('segment_type')

    permission_classes = [
        TenantConditionalOpenClose,
    ]
