import mimetypes

import magic
from django.conf import settings
from django.http import HttpResponse
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from sorl.thumbnail.shortcuts import get_thumbnail

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.files.models import Document
from bluebottle.files.serializers import FileSerializer, ImageSerializer
from bluebottle.initiatives.models import Initiative
from bluebottle.utils.views import CreateAPIView, RetrieveAPIView

mime = magic.Magic(mime=True)


class FileList(AutoPrefetchMixin, CreateAPIView):
    queryset = Document.objects.all()
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
        uploaded_file = self.request.FILES['file']
        if not mime.from_buffer(uploaded_file.read()) == uploaded_file.content_type:
            raise ValidationError('Mime-type does not match Content-Type')

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

        return response


class ImageList(FileList):
    queryset = Initiative.objects.all()
    serializer_class = ImageSerializer
