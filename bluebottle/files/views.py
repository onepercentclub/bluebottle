import mimetypes

from django.conf import settings
from django.http import HttpResponse

from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated

from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.views import AutoPrefetchMixin

from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from sorl.thumbnail.shortcuts import get_thumbnail

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.files.models import File
from bluebottle.files.serializers import FileSerializer
from bluebottle.utils.views import CreateAPIView, RetrieveAPIView


class FileList(AutoPrefetchMixin, CreateAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    renderer_classes = (BluebottleJSONAPIRenderer, )
    parser_classes = (FileUploadParser,)
    permission_classes = (IsAuthenticated, )

    authentication_classes = (
       JSONWebTokenAuthentication,
    )

    prefetch_for_includes = {
        'owner': ['owner'],
    }

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class FileContentView(RetrieveAPIView):
    def retrieve(self, *args, **kwargs):
        instance = self.get_object()

        file = getattr(instance, self.field).file

        thumbnail = get_thumbnail(file, self.kwargs['size'])
        content_type = mimetypes.guess_type(file.name)[0]

        if settings.DEBUG:
            response = HttpResponse(content=thumbnail.read())
        else:
            response = HttpResponse()
            response['X-Accel-Redirect'] = thumbnail.url

        response['Content-Type'] = content_type
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            file
        )

        return response
