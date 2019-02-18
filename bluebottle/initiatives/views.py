from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, CreateAPIView
)
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)

from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.pagination import JsonApiPageNumberPagination

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.serializers import InitiativeSerializer, TransitionSerializer
from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer


class InitiativePagination(JsonApiPageNumberPagination):
    page_size = 8



class TransitionList(CreateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = TransitionSerializer

    parser_classes = (JSONParser, )
    renderer_classes = (BluebottleJSONAPIRenderer, )

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )


class InitiativeList(ListCreateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer
    pagination_class = InitiativePagination

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
    parser_classes = (JSONParser, )

    renderer_classes = (BluebottleJSONAPIRenderer, )

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer']
    }

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class InitiativeDetail(AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    parser_classes = (JSONParser, )
    renderer_classes = (BluebottleJSONAPIRenderer, )

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer']
    }


