from rest_framework_json_api import django_filters
from rest_framework_json_api.exceptions import exception_handler
from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.files.views import FileContentView
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.serializers import InitiativeSerializer
from bluebottle.utils.permissions import ResourceOwnerPermission
from bluebottle.utils.views import ListCreateAPIView, RetrieveUpdateAPIView


class InitiativePagination(JsonApiPageNumberPagination):
    page_size = 8


class InitiativeList(AutoPrefetchMixin, ListCreateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer
    pagination_class = InitiativePagination

    permission_classes = (ResourceOwnerPermission,)

    filter_backends = (
        django_filters.DjangoFilterBackend,
    )
    filter_fields = {
        'owner__id': ('exact', 'in',),
    }
    authentication_classes = (
        JSONWebTokenAuthentication,
    )

    parser_classes = (JSONParser,)

    renderer_classes = (BluebottleJSONAPIRenderer,)

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer'],
        'theme': ['theme'],
        'place': ['place'],
        'categories': ['categories'],
        'image': ['image'],
    }

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class InitiativeDetail(AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer

    permission_classes = (ResourceOwnerPermission,)

    authentication_classes = (
        JSONWebTokenAuthentication,
    )

    def get_exception_handler(self):
        return exception_handler

    parser_classes = (JSONParser,)
    renderer_classes = (BluebottleJSONAPIRenderer,)

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer'],
        'theme': ['theme'],
        'place': ['place'],
        'categories': ['categories'],
        'image': ['image'],
    }


class InitiativeImage(FileContentView):
    queryset = Initiative.objects
    field = 'image'
