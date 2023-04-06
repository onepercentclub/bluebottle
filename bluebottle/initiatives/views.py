import uuid
from builtins import str

from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point
from django.core.cache import cache
from django.db import connection
from rest_framework import generics, response
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.bluebottle_drf2.renderers import ElasticSearchJSONAPIRenderer
from bluebottle.files.models import RelatedImage
from bluebottle.files.views import ImageContentView
from bluebottle.funding.models import Funding
from bluebottle.initiatives.filters import InitiativeSearchFilter
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.models import Theme
from bluebottle.initiatives.permissions import (
    InitiativeStatusPermission, InitiativeOwnerPermission
)
from bluebottle.initiatives.serializers import (
    InitiativeSerializer, InitiativeListSerializer, InitiativeReviewTransitionSerializer,
    InitiativeMapSerializer, InitiativePreviewSerializer, InitiativeRedirectSerializer,
    RelatedInitiativeImageSerializer, ThemeSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission, TenantConditionalOpenClose
)
from bluebottle.utils.views import (
    RetrieveUpdateAPIView, JsonApiViewMixin,
    CreateAPIView, ListAPIView, TranslatedApiViewMixin, RetrieveAPIView, NoPagination,
    JsonApiElasticSearchPagination,
)


class InitiativeList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    queryset = Initiative.objects.prefetch_related(
        'place', 'location', 'owner', 'activity_managers', 'image', 'categories', 'theme'
    )

    def get_serializer_class(self):
        if self.request.method == 'POST' or self.request.GET.get('filter[owner.id]'):
            return InitiativeSerializer
        else:
            return InitiativeListSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    filterset_fields = {
        'owner__id': ('exact', 'in',),
    }

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer'],
        'promoter': ['promoter'],
        'activity_managers': ['activity_managers'],
        'theme': ['theme'],
        'place': ['place'],
        'location': ['location'],
        'categories': ['categories'],
        'image': ['image'],
        'organization': ['organization'],
        'organization_contact': ['organization_contact'],
    }

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(owner=self.request.user, **serializer.validated_data)
        )

        serializer.save(owner=self.request.user)


class InitiativePreviewList(JsonApiViewMixin, ListAPIView):
    serializer_class = InitiativePreviewSerializer
    model = Initiative
    pagination_class = JsonApiElasticSearchPagination
    renderer_classes = (ElasticSearchJSONAPIRenderer, )
    filter_backends = (
        InitiativeSearchFilter,
    )

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    def list(self, request, *args, **kwargs):
        result = self.filter_queryset(None)

        page = self.paginate_queryset(result)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(result, many=True)
        return response.Response(serializer.data)


class TinyProjectPagination(PageNumberPagination):
    page_size = 10000


class InitiativeMapList(generics.ListAPIView):
    queryset = Initiative.objects
    serializer_class = InitiativeMapSerializer

    owner_filter_field = 'owner'

    def get_queryset(self):
        queryset = super(InitiativeMapList, self).get_queryset()
        queryset = queryset.filter(status='approved').all()
        queryset = queryset.exclude(place__position=Point(0, 0))
        return queryset

    def list(self, request, *args, **kwargs):
        cache_key = '{}.initiative_preview_data'.format(connection.tenant.schema_name)
        cache.set(cache_key, None)
        data = cache.get(cache_key)
        if not data:
            queryset = self.get_queryset().order_by('created')
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            cache.set(cache_key, data)
        return Response(data)


class InitiativeDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Initiative.objects.select_related(
        'owner', 'reviewer', 'promoter', 'place', 'location',
        'organization', 'organization_contact',
    ).prefetch_related(
        'categories', 'activities'
    )

    serializer_class = InitiativeSerializer

    permission_classes = (
        InitiativeStatusPermission,
        OneOf(ResourcePermission, InitiativeOwnerPermission),
    )

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer'],
        'promoter': ['promoter'],
        'theme': ['theme'],
        'place': ['place'],
        'location': ['location'],
        'categories': ['categories'],
        'image': ['image'],
        'organization': ['organization'],
        'organization_contact': ['organization_contact'],
        'activities': ['activities'],
    }


class InitiativeImage(ImageContentView):
    queryset = Initiative.objects
    field = 'image'


class RelatedInitiativeImageList(JsonApiViewMixin, AutoPrefetchMixin, CreateAPIView):
    def get_queryset(self):
        return RelatedImage.objects.filter(
            content_type=ContentType.objects.get_for_model(Initiative)
        )

    serializer_class = RelatedInitiativeImageSerializer

    related_permission_classes = {
        'content_object': [ResourceOwnerPermission]
    }

    permission_classes = []


class RelatedInitiativeImageContent(ImageContentView):
    queryset = RelatedImage.objects
    field = 'image'


class InitiativeReviewTransitionList(TransitionList):
    serializer_class = InitiativeReviewTransitionSerializer
    queryset = Initiative.objects.all()


class ThemeList(TranslatedApiViewMixin, JsonApiViewMixin, ListAPIView):
    serializer_class = ThemeSerializer
    queryset = Theme.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]
    pagination_class = NoPagination

    def get_queryset(self):
        return super().get_queryset()


class ThemeDetail(TranslatedApiViewMixin, JsonApiViewMixin, RetrieveAPIView):
    serializer_class = ThemeSerializer
    queryset = Theme.objects.filter(disabled=False)
    permission_classes = [TenantConditionalOpenClose, ]


from collections import namedtuple

Instance = namedtuple('Instance', 'pk, route, params, target_params, target_route')


class InitiativeRedirectList(JsonApiViewMixin, CreateAPIView):
    serializer_class = InitiativeRedirectSerializer
    permission_classes = ()

    def perform_create(self, serializer):
        data = serializer.validated_data
        data['pk'] = str(uuid.uuid1())

        if data['route'] == 'project':
            initiative = Initiative.objects.filter(slug=data['params']['project_id']).first()
            if not initiative:
                raise NotFound()

            try:
                funding = initiative.activities.instance_of(Funding)[0]
                data['target_route'] = 'initiatives.activities.details.funding'
                data['target_params'] = [funding.pk, funding.slug]
            except IndexError:
                data['target_route'] = 'initiatives.details'
                data['target_params'] = [initiative.pk, initiative.slug]
        else:
            raise NotFound()

        serializer.instance = Instance(**data)
        return data
