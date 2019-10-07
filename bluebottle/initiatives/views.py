from django.core.cache import cache
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_json_api.views import AutoPrefetchMixin

from bluebottle.files.views import ImageContentView
from bluebottle.initiatives.filters import InitiativeSearchFilter
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.permissions import InitiativePermission
from bluebottle.initiatives.serializers import (
    InitiativeSerializer, InitiativeReviewTransitionSerializer,
    InitiativeMapSerializer)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin)


class InitiativeList(JsonApiViewMixin, AutoPrefetchMixin, ListCreateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer

    permission_classes = (InitiativePermission,)

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
        serializer.save(owner=self.request.user)


class TinyProjectPagination(PageNumberPagination):
    page_size = 10000


class InitiativeMapList(generics.ListAPIView):
    queryset = Initiative.objects.filter(status='approved').all()
    serializer_class = InitiativeMapSerializer

    owner_filter_field = 'owner'

    def list(self, request):
        data = cache.get('initiative_map_data')
        if not data:
            result = self.queryset.order_by('-created')
            serializer = self.get_serializer(result, many=True)
            data = serializer.data
            cache.set('initiative_map_data', data)
        return Response(data)


class InitiativeDetail(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeSerializer
    permission_classes = (InitiativePermission,)

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


class InitiativeReviewTransitionList(TransitionList):
    serializer_class = InitiativeReviewTransitionSerializer
    queryset = Initiative.objects.all()
