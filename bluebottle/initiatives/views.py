from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.pagination import JsonApiPageNumberPagination

from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.utils.views import ListCreateAPIView, RetrieveUpdateAPIView
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.serializers import InitiativeSerializer
from bluebottle.files.views import FileContentView
from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer


class InitiativePagination(JsonApiPageNumberPagination):
    page_size = 8


class InitiativeList(AutoPrefetchMixin, ListCreateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer
    pagination_class = InitiativePagination

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )
    authentication_classes = (
       JSONWebTokenAuthentication,
    )

    parser_classes = (JSONParser, )

    renderer_classes = (BluebottleJSONAPIRenderer, )

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer'],
        'theme': ['theme'],
        'categories': ['categories'],
        'image': ['image'],
    }

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class InitiativeDetail(AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    authentication_classes = (
       JSONWebTokenAuthentication,
    )


    parser_classes = (JSONParser, )
    renderer_classes = (BluebottleJSONAPIRenderer, )

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer'],
        'theme': ['theme'],
        'categories': ['categories'],
        'image': ['image'],
    }


class InitiativeImage(FileContentView):
    queryset = Initiative.objects
    field = 'image'
