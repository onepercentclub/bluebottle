from bluebottle.time_based.models import Interest
from bluebottle.time_based.serializers.interests import InterestSerializer
from bluebottle.utils.permissions import ResourceOwnerPermission
from bluebottle.utils.views import (
    CreateAPIView,
    JsonApiViewMixin,
    RetrieveUpdateDestroyAPIView,
)


class InterestList(JsonApiViewMixin, CreateAPIView):
    queryset = Interest.objects.prefetch_related('user', 'activity', 'slot')
    serializer_class = InterestSerializer
    permission_classes = (ResourceOwnerPermission,)


class InterestDetail(JsonApiViewMixin, RetrieveUpdateDestroyAPIView):
    queryset = Interest.objects.prefetch_related('user', 'activity', 'slot')
    serializer_class = InterestSerializer
    http_method_names = ['get', 'delete', 'head', 'options']
    permission_classes = (ResourceOwnerPermission,)
