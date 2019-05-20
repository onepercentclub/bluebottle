from rest_framework_json_api.exceptions import exception_handler
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.files.views import FileContentView
from bluebottle.initiatives.filters import InitiativeSearchFilter
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.serializers import (
    InitiativeSerializer, InitiativeReviewTransitionSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import ResourceOwnerPermission
from bluebottle.utils.views import ListCreateAPIView, RetrieveUpdateAPIView, JsonApiPagination, JsonApiViewMixin


class InitiativeList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer
    pagination_class = JsonApiPagination

    permission_classes = (ResourceOwnerPermission,)

    filter_backends = (
        InitiativeSearchFilter,
    )
    authentication_classes = (
        JSONWebTokenAuthentication,
    )

    parser_classes = (JSONParser,)

    renderer_classes = (BluebottleJSONAPIRenderer,)

    filter_fields = {
        'owner__id': ('exact', 'in',),
    }

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer'],
        'promoter': ['promoter'],
        'theme': ['theme'],
        'place': ['place'],
        'categories': ['categories'],
        'image': ['image'],
        'organization': ['organization'],
        'organization_contact': ['organization_contact'],
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
        'promoter': ['promoter'],
        'theme': ['theme'],
        'place': ['place'],
        'categories': ['categories'],
        'image': ['image'],
        'organization': ['organization'],
        'organization_contact': ['organization_contact'],
    }


class InitiativeImage(FileContentView):
    queryset = Initiative.objects
    field = 'image'


class InitiativeReviewTransitionList(TransitionList):
    serializer_class = InitiativeReviewTransitionSerializer
    queryset = Initiative.objects.all()
