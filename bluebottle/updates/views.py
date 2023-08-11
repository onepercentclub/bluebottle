from rest_framework import permissions

from bluebottle.files.views import ImageContentView
from bluebottle.updates.models import Update, UpdateImage
from bluebottle.updates.serializers import UpdateSerializer, UpdateImageListSerializer
from bluebottle.utils.permissions import TenantConditionalOpenClose
from bluebottle.utils.views import (
    CreateAPIView, RetrieveUpdateDestroyAPIView, JsonApiViewMixin, ListAPIView
)


class ActivityOwnerUpdatePermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user is author of the update, `False` otherwise.
        """
        return obj.author == obj.activity.owner or (not obj.notify and not obj.pinned)


class UpdateList(JsonApiViewMixin, CreateAPIView):
    queryset = Update.objects.all()
    serializer_class = UpdateSerializer

    permission_classes = (permissions.IsAuthenticated, ActivityOwnerUpdatePermission)

    def perform_create(self, serializer):
        if hasattr(serializer.Meta, 'model'):
            self.check_object_permissions(
                self.request,
                serializer.Meta.model(author=self.request.user, **serializer.validated_data)
            )

        serializer.save(author=self.request.user)


class UpdateImageList(JsonApiViewMixin, CreateAPIView):
    queryset = UpdateImage.objects.all()
    serializer_class = UpdateImageListSerializer
    permission_classes = (permissions.IsAuthenticated,)


class IsAuthorPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user is author of the update, `False` otherwise.
        """
        return obj.author == request.user


class UpdateDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = Update.objects.all()
    serializer_class = UpdateSerializer

    permission_classes = [
        IsAuthorPermission
    ]


class ActivityUpdateList(JsonApiViewMixin, ListAPIView):
    permission_classes = [TenantConditionalOpenClose]
    queryset = Update.objects.order_by('pinned', '-created')

    def get_queryset(self):
        return super().get_queryset().filter(
            activity_id=self.kwargs['activity_pk']
        )

    serializer_class = UpdateSerializer


class UpdateImageContent(ImageContentView):
    queryset = UpdateImage.objects
    field = 'image'
