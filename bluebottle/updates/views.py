from rest_framework import permissions
from rest_framework.throttling import UserRateThrottle


from bluebottle.files.views import ImageContentView
from bluebottle.updates.models import Update, UpdateImage
from bluebottle.updates.permissions import IsAuthorPermission, ActivityOwnerUpdatePermission, \
    UpdateRelatedActivityPermission, IsStaffMember
from bluebottle.updates.serializers import UpdateSerializer, UpdateImageListSerializer
from bluebottle.utils.permissions import TenantConditionalOpenClose, OneOf
from bluebottle.utils.views import (
    CreateAPIView, RetrieveUpdateDestroyAPIView, JsonApiViewMixin, ListAPIView
)


class UpdateThrottle(UserRateThrottle):
    def allow_request(self, request, view):
        try:
            if request.data['notify']:
                return super().allow_request(request, view)
        except KeyError:
            pass

        return True


class UpdateList(JsonApiViewMixin, CreateAPIView):
    queryset = Update.objects.all()
    serializer_class = UpdateSerializer

    permission_classes = (
        permissions.IsAuthenticated,
        ActivityOwnerUpdatePermission
    )
    throttle_classes = [UpdateThrottle]

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


class UpdateDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = Update.objects.all()
    serializer_class = UpdateSerializer

    permission_classes = [
        OneOf(IsAuthorPermission, UpdateRelatedActivityPermission, IsStaffMember)
    ]


class ActivityUpdateList(JsonApiViewMixin, ListAPIView):
    permission_classes = [TenantConditionalOpenClose]
    queryset = Update.objects.order_by('-pinned', '-created')

    def get_queryset(self):
        return super().get_queryset().filter(
            activity_id=self.kwargs['activity_pk']
        ).filter(parent__isnull=True)

    serializer_class = UpdateSerializer


class UpdateImageContent(ImageContentView):
    allowed_sizes = {
        'preview': '292x164',
        'large': '1600x900',
    }

    queryset = UpdateImage.objects
    field = 'image'
