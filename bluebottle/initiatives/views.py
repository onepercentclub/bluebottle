import uuid
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.geos import Point

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import generics
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.files.views import ImageContentView
from bluebottle.funding.models import Funding
from bluebottle.activities.models import Activity
from bluebottle.files.models import RelatedImage
from bluebottle.geo.models import Location
from bluebottle.initiatives.filters import InitiativeSearchFilter
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.serializers import (
    InitiativeSerializer, InitiativeReviewTransitionSerializer,
    InitiativeMapSerializer, InitiativeRedirectSerializer,
    RelatedInitiativeImageSerializer
)
from bluebottle.tasks.models import Task
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin,
    CreateAPIView,
)


class InitiativeList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
    )

    filter_backends = (
        InitiativeSearchFilter,
    )

    filter_fields = {
        'owner__id': ('exact', 'in',),
    }

    prefetch_for_includes = {
        'owner': ['owner'],
        'reviewer': ['reviewer'],
        'promoter': ['promoter'],
        'activity_manager': ['activity_manager'],
        'theme': ['theme'],
        'place': ['place'],
        'location': ['location'],
        'categories': ['categories'],
        'image': ['image'],
        'organization': ['organization'],
        'organization_contact': ['organization_contact'],
        'activities': ['activities'],
    }

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save(owner=self.request.user)


class TinyProjectPagination(PageNumberPagination):
    page_size = 10000


class InitiativeMapList(generics.ListAPIView):
    queryset = Initiative.objects
    serializer_class = InitiativeMapSerializer

    owner_filter_field = 'owner'

    def get_queryset(self):
        queryset = super(InitiativeMapList, self).get_queryset()
        queryset = queryset.filter(status='approved').all()
        if not Location.objects.count():
            # Skip initiatives without proper location
            queryset = queryset.exclude(place__position=Point(0, 0))
        return queryset

    def list(self, request, *args, **kwargs):
        cache_key = '{}.initiative_map_data'.format(connection.tenant.schema_name)
        data = cache.get(cache_key)
        if not data:
            queryset = self.get_queryset().order_by('created')
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            cache.set(cache_key, data)
        return Response(data)


class InitiativeDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer

    permission_classes = (
        OneOf(ResourcePermission, ResourceOwnerPermission),
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


from collections import namedtuple
Instance = namedtuple('Instance', 'pk, route, params, target_params, target_route')


class InitiativeRedirectList(JsonApiViewMixin, CreateAPIView):
    serializer_class = InitiativeRedirectSerializer
    permission_classes = ()

    def perform_create(self, serializer):
        data = serializer.validated_data
        data['pk'] = str(uuid.uuid1())

        try:
            if data['route'] == 'project':
                initiative = Initiative.objects.get(slug=data['params']['project_id'])
                try:
                    funding = initiative.activities.instance_of(Funding)[0]
                    data['target_route'] = 'initiatives.activities.details.funding'
                    data['target_params'] = [funding.pk, funding.slug]
                except IndexError:
                    data['target_route'] = 'initiatives.details'
                    data['target_params'] = [initiative.pk, initiative.slug]
            elif data['route'] == 'task':
                task = Task.objects.get(id=data['params']['task_id'])
                activity = Activity.objects.get(pk=task.activity_id)
                data['target_route'] = 'initiatives.activities.details.{}'.format(
                    'event' if task.type == 'event' else 'assignment'
                )
                data['target_params'] = [activity.pk, activity.slug]
            else:
                raise NotFound()

            serializer.instance = Instance(**data)
            return data
        except ObjectDoesNotExist:
            raise NotFound()
