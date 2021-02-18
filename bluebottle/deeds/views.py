from bluebottle.activities.permissions import (
    ActivityOwnerPermission, ActivityTypePermission, ActivityStatusPermission,
    DeleteActivityPermission
)
from bluebottle.deeds.models import Deed
from bluebottle.deeds.serializers import DeedSerializer, DeedTransitionSerializer
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission
)
from bluebottle.utils.views import (
    RetrieveUpdateDestroyAPIView, ListCreateAPIView,
    JsonApiViewMixin
)


class DeedListView(JsonApiViewMixin, ListCreateAPIView):
    queryset = Deed.objects.all()
    serializer_class = DeedSerializer

    permission_classes = (
        ActivityTypePermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
    )

    def perform_create(self, serializer):
        self.check_related_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )
        serializer.save(owner=self.request.user)


class DeedDetailView(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    permission_classes = (
        ActivityStatusPermission,
        OneOf(ResourcePermission, ActivityOwnerPermission),
        DeleteActivityPermission
    )

    queryset = Deed.objects.all()
    serializer_class = DeedSerializer


class DeedTransitionList(TransitionList):
    serializer_class = DeedTransitionSerializer
    queryset = Deed.objects.all()
