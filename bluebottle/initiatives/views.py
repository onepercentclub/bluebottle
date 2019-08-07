from rest_framework import response
from rest_framework_json_api.views import AutoPrefetchMixin


from bluebottle.files.views import FileContentView
from bluebottle.initiatives.filters import InitiativeSearchFilter
from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.permissions import InitiativePermission
from bluebottle.initiatives.serializers import (
    InitiativeSerializer, InitiativeReviewTransitionSerializer,
    InitiativeValidationSerializer
)
from bluebottle.transitions.views import TransitionList
from bluebottle.utils.views import (
    ListCreateAPIView, RetrieveUpdateAPIView, JsonApiViewMixin
)


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


class InitiativeValidation(JsonApiViewMixin, AutoPrefetchMixin, RetrieveUpdateAPIView):
    queryset = Initiative.objects.all()
    serializer_class = InitiativeValidationSerializer
    permission_classes = (InitiativePermission,)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)

        return response.Response(serializer.data)


class InitiativeImage(FileContentView):
    queryset = Initiative.objects
    field = 'image'


class InitiativeReviewTransitionList(TransitionList):
    serializer_class = InitiativeReviewTransitionSerializer
    queryset = Initiative.objects.all()
