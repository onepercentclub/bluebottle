from rest_framework import generics
from rest_framework import filters
from rest_framework import response

from bluebottle.updates.permissions import IsStaffMember
from bluebottle.utils.permissions import (
    IsAuthenticated, IsOwnerOrReadOnly, IsOwner, OneOf, TenantConditionalOpenClose
)

from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.views import AutoPrefetchMixin

from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from bluebottle.utils.views import (
    ListAPIView, JsonApiViewMixin, JsonApiElasticSearchPagination,
)

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer, ElasticSearchJSONAPIRenderer

from bluebottle.organizations.filters import OrganizationSearchFilter
from bluebottle.organizations.serializers import (
    OrganizationSerializer, OrganizationDetailSerializer, OrganizationContactSerializer,
    OrganizationPreviewSerializer
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


class OrganizationContactDetail(AutoPrefetchMixin, generics.RetrieveUpdateAPIView):
    queryset = OrganizationContact.objects.all()
    serializer_class = OrganizationContactSerializer

    renderer_classes = (BluebottleJSONAPIRenderer, )
    parser_classes = (JSONParser, )
    permission_classes = (IsAuthenticated, IsOwner)
    authentication_classes = (
        JSONWebTokenAuthentication,
    )


class OrganizationPreviewList(JsonApiViewMixin, ListAPIView):
    serializer_class = OrganizationPreviewSerializer
    model = Organization
    pagination_class = JsonApiElasticSearchPagination
    renderer_classes = (ElasticSearchJSONAPIRenderer,)

    def list(self, request, *args, **kwargs):
        result = self.filter_queryset(None)

        page = self.paginate_queryset(result)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(result, many=True)
        return response.Response(serializer.data)

    filter_backends = (
        OrganizationSearchFilter,
    )

    permission_classes = (
        TenantConditionalOpenClose,
        OneOf(IsOwnerOrReadOnly, IsStaffMember),
    )


class OrganizationSearchFilter(filters.SearchFilter):
    search_param = "filter[search]"


class OrganizationList(AutoPrefetchMixin, generics.ListCreateAPIView):
    model = Organization
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

    prefetch_for_includes = {
        'owner': ['owner'],
    }


class OrganizationDetail(AutoPrefetchMixin, generics.RetrieveUpdateAPIView):
    model = Organization
    queryset = Organization.objects.all()
    serializer_class = OrganizationDetailSerializer
    permission_classes = (
        TenantConditionalOpenClose,
        OneOf(IsOwnerOrReadOnly, IsStaffMember),
    )
    renderer_classes = (BluebottleJSONAPIRenderer, )
    parser_classes = (JSONParser, )
    authentication_classes = (
        JSONWebTokenAuthentication,
    )
