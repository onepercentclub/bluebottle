from rest_framework import generics
from rest_framework import filters

from rest_framework.permissions import IsAuthenticated

from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.views import AutoPrefetchMixin

from rest_framework_jwt.authentication import JSONWebTokenAuthentication


from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer

from bluebottle.organizations.serializers import (
    OrganizationSerializer, OrganizationContactSerializer
)
from bluebottle.organizations.models import (
    Organization, OrganizationContact
)


class OrganizationPagination(JsonApiPageNumberPagination):
    page_size = 8


class OrganizationContactList(AutoPrefetchMixin, generics.CreateAPIView):
    queryset = OrganizationContact.objects.all()
    serializer_class = OrganizationContactSerializer
    permission_classes = (IsAuthenticated, )
    filter_backends = (filters.SearchFilter,)
    search_fields = ['name']
    renderer_classes = (BluebottleJSONAPIRenderer, )
    parser_classes = (JSONParser, )
    authentication_classes = (
        JSONWebTokenAuthentication,
    )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class OrganizationContactDetail(AutoPrefetchMixin, generics.RetrieveUpdateAPIView):
    queryset = OrganizationContact.objects.all()
    serializer_class = OrganizationContactSerializer

    renderer_classes = (BluebottleJSONAPIRenderer, )
    parser_classes = (JSONParser, )
    permission_classes = (IsAuthenticated, )
    authentication_classes = (
        JSONWebTokenAuthentication,
    )


class OrganizationSearchFilter(filters.SearchFilter):
    search_param = "filter[search]"


class OrganizationList(AutoPrefetchMixin, generics.ListCreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    pagination_class = OrganizationPagination

    filter_backends = (OrganizationSearchFilter, )

    search_fields = ['name']

    permission_classes = (IsAuthenticated,)
    renderer_classes = (BluebottleJSONAPIRenderer, )
    parser_classes = (JSONParser, )

    authentication_classes = (
        JSONWebTokenAuthentication,
    )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    prefetch_for_includes = {
        'owner': ['owner'],
    }


class OrganizationDetail(AutoPrefetchMixin, generics.RetrieveUpdateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = (IsAuthenticated,)
    renderer_classes = (BluebottleJSONAPIRenderer, )
    parser_classes = (JSONParser, )
    authentication_classes = (
        JSONWebTokenAuthentication,
    )
