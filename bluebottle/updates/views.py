from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from bluebottle.activities.models import Activity
from bluebottle.files.serializers import ORIGINAL_SIZE
from bluebottle.files.views import FileContentView, ImageContentView
from bluebottle.updates.models import Update, UpdateDocument, UpdateImage, AudienceChoices
from bluebottle.updates.permissions import (
    IsAuthorPermission, ActivityOwnerUpdatePermission,
    UpdateRelatedActivityPermission, IsStaffMember,
    CanPostUpdatePermission, ContributorAudiencePermission,
)
from bluebottle.updates.serializers import (
    UpdateSerializer, UpdateImageListSerializer, UpdateDocumentListSerializer
)
from bluebottle.updates.utils import get_effective_audience, user_can_view_contributor_updates
from bluebottle.utils.permissions import TenantConditionalOpenClose, OneOf
from bluebottle.utils.views import (
    CreateAPIView, RetrieveUpdateDestroyAPIView, JsonApiViewMixin, ListAPIView
)


class UpdateThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        if request.user.is_superuser:
            return True

        try:
            if request.data['notify']:
                return super().allow_request(request, view)
        except KeyError:
            pass

        return True


class UpdateList(JsonApiViewMixin, CreateAPIView):
    queryset = Update.objects.all()
    serializer_class = UpdateSerializer
    related_permission_classes = {
        'activity': [CanPostUpdatePermission]
    }

    permission_classes = (
        permissions.IsAuthenticated,
        ActivityOwnerUpdatePermission,
    )
    throttle_classes = [UpdateThrottle]

    def perform_create(self, serializer):
        if hasattr(serializer.Meta, 'model'):
            self.check_object_permissions(
                self.request,
                serializer.Meta.model(author=self.request.user, **serializer.validated_data)
            )

        serializer.validated_data['author'] = self.request.user
        super().perform_create(serializer)


class UpdateImageList(JsonApiViewMixin, CreateAPIView):
    queryset = UpdateImage.objects.all()
    serializer_class = UpdateImageListSerializer
    permission_classes = (permissions.IsAuthenticated,)


class UpdateDocumentList(JsonApiViewMixin, CreateAPIView):
    queryset = UpdateDocument.objects.all()
    serializer_class = UpdateDocumentListSerializer
    permission_classes = (permissions.IsAuthenticated,)


class UpdateDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = Update.objects.all()
    serializer_class = UpdateSerializer

    permission_classes = [
        ContributorAudiencePermission,
        OneOf(IsAuthorPermission, UpdateRelatedActivityPermission, IsStaffMember)
    ]

    def check_object_permissions(self, request, obj):
        if (
            request.method in SAFE_METHODS
            and get_effective_audience(obj) == AudienceChoices.contributors
            and not user_can_view_contributor_updates(request.user, obj.activity)
        ):
            raise PermissionDenied()
        super().check_object_permissions(request, obj)


class ActivityUpdateList(JsonApiViewMixin, ListAPIView):
    permission_classes = [TenantConditionalOpenClose]
    queryset = Update.objects.order_by('-pinned', '-created')

    def get_activity(self):
        if not hasattr(self, '_activity'):
            self._activity = Activity.objects.get(pk=self.kwargs['activity_pk'])
        return self._activity

    def get_visible_queryset(self):
        queryset = self.queryset.filter(
            activity_id=self.kwargs['activity_pk'],
            parent__isnull=True,
        )
        if not user_can_view_contributor_updates(self.request.user, self.get_activity()):
            queryset = queryset.filter(audience=AudienceChoices.everyone)
        return queryset

    def get_queryset(self):
        queryset = self.get_visible_queryset()
        audience_filter = self.request.query_params.get('filter[audience]')
        if audience_filter in (AudienceChoices.everyone, AudienceChoices.contributors):
            queryset = queryset.filter(audience=audience_filter)
        return queryset

    def list(self, request, *args, **kwargs):
        visible_queryset = self.get_visible_queryset()
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
        else:
            serializer = self.get_serializer(queryset, many=True)
            response = Response(serializer.data)

        if user_can_view_contributor_updates(request.user, self.get_activity()):
            response.data['meta']['audience'] = {
                'all': visible_queryset.count(),
                'everyone': visible_queryset.filter(
                    audience=AudienceChoices.everyone
                ).count(),
                'contributors': visible_queryset.filter(
                    audience=AudienceChoices.contributors
                ).count(),
            }
        return response

    serializer_class = UpdateSerializer


class UpdateImageContent(ImageContentView):
    allowed_sizes = {
        'small': '150x150',
        'medium': '800x450',
        'large': '1600x900',
        'full': ORIGINAL_SIZE,
    }

    queryset = UpdateImage.objects
    field = 'image'


class UpdateDocumentContent(FileContentView):
    queryset = UpdateDocument.objects
    field = 'document'
