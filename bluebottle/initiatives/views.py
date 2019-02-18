import mimetypes

from django.http import Http404, HttpResponse

from bluebottle.utils.views import ListCreateAPIView, RetrieveUpdateAPIView, RetrieveAPIView
from bluebottle.utils.permissions import (
    OneOf, ResourcePermission, ResourceOwnerPermission
)

from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.pagination import JsonApiPageNumberPagination

from sorl.thumbnail.shortcuts import get_thumbnail

from bluebottle.initiatives.models import Initiative
from bluebottle.initiatives.serializers import InitiativeSerializer
from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer


class InitiativePagination(JsonApiPageNumberPagination):
    page_size = 8


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


class InitiativeImage(RetrieveAPIView):
    queryset = Initiative.objects

    def retrieve(self, *args, **kwargs):
        instance = self.get_object()

        thumbnail = get_thumbnail(instance.image.file, self.kwargs['size'])
        content_type = mimetypes.guess_type(instance.image.file.name)[0]

        response = HttpResponse()

        response['X-Accel-Redirect'] = thumbnail.url
        response['Content-Type'] = content_type
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            instance.image.file.name
        )

        return response
