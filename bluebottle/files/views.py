import mimetypes
from os.path import exists
from random import randrange

import magic
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from sorl.thumbnail.shortcuts import get_thumbnail

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.files.models import Document, Image, PrivateDocument
from bluebottle.files.serializers import FileSerializer, ImageSerializer, PrivateFileSerializer
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

    allowed_mime_types = settings.PRIVATE_FILE_ALLOWED_MIME_TYPES

    def perform_create(self, serializer):
        uploaded_file = self.request.FILES['file']
        mime_type = mime.from_buffer(uploaded_file.read())
        if not mime_type == uploaded_file.content_type:
            raise ValidationError('Mime-type does not match Content-Type')

        if mime_type not in self.allowed_mime_types:
            raise ValidationError('Mime-type is not allowed for this endpoint')

        serializer.save(owner=self.request.user)


class PrivateFileList(FileList):
    queryset = PrivateDocument.objects.all()
    serializer_class = PrivateFileSerializer


class FileContentView(RetrieveAPIView):

    permission_classes = []

    def retrieve(self, *args, **kwargs):
        instance = self.get_object()
        file = getattr(instance, self.field).file
        content_type = mimetypes.guess_type(file.name)[0]

        if settings.DEBUG:
            response = HttpResponse(content=file.read())
        else:
            response = HttpResponse()
            response['X-Accel-Redirect'] = file.url

        response['Content-Type'] = content_type

        return response


class ImageContentView(FileContentView):

    def get_random_image_url(self):
        if 'x' in self.kwargs['size']:
            width, height = self.kwargs['size'].split('x')
        else:
            width = self.kwargs['size']
            height = int(int(width) / 1.5)
        return settings.RANDOM_IMAGE_PROVIDER.format(seed=randrange(1, 300), width=width, height=height)

    def retrieve(self, *args, **kwargs):

        instance = self.get_object()
        file = getattr(instance, self.field).file

        # import ipdb; ipdb.set_trace()

        if 'x' in self.kwargs['size']:
            if self.kwargs['size'] not in self.allowed_sizes.values():
                return HttpResponseNotFound()
        else:
            if not self.kwargs['size'] in [val.split('x')[0] for val in self.allowed_sizes.values()]:
                return HttpResponseNotFound()

        thumbnail = get_thumbnail(file, self.kwargs['size'])
        content_type = mimetypes.guess_type(file.name)[0]

        if settings.DEBUG:
            try:
                response = HttpResponse(content=thumbnail.read())
                response['Content-Type'] = content_type
            except FileNotFoundError:
                if settings.RANDOM_IMAGE_PROVIDER:
                    response = HttpResponseRedirect(self.get_random_image_url())
                else:
                    response = HttpResponseNotFound()
        else:
            response = HttpResponse()
            if exists(file.path):
                response['Content-Type'] = content_type
                response['X-Accel-Redirect'] = thumbnail.url
            elif settings.RANDOM_IMAGE_PROVIDER:
                response = HttpResponseRedirect(self.get_random_image_url())
            else:
                response = HttpResponseNotFound()
        return response


class ImageList(FileList):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    allowed_mime_types = settings.IMAGE_ALLOWED_MIME_TYPES
