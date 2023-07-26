from bluebottle.files.views import ImageContentView

from bluebottle.updates.models import Update
from bluebottle.updates.serializers import UpdateSerializer

from bluebottle.utils.permissions import TenantConditionalOpenClose
from bluebottle.utils.views import (
    CreateAPIView, RetrieveUpdateDestroyAPIView, JsonApiViewMixin, ListAPIView
)

from rest_framework import permissions


class ActivityOwnerUpdatePermision(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        """
        Return `True` if user is author of the update, `False` otherwise.
        """
        return obj.author == obj.activity.owner or (not obj.notify and not obj.pinned)


class UpdateList(JsonApiViewMixin, CreateAPIView):
    queryset = Update.objects.all()
    serializer_class = UpdateSerializer

    permission_classes = (permissions.IsAuthenticated, ActivityOwnerUpdatePermision)

    def perform_create(self, serializer):
        if hasattr(serializer.Meta, 'model'):
            self.check_object_permissions(
                self.request,
                serializer.Meta.model(author=self.request.user, **serializer.validated_data)
            )

        serializer.save(author=self.request.user)


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
    queryset = Update.objects
    field = 'image'
