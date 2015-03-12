import os

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.http.response import HttpResponseForbidden, HttpResponseNotFound
from django.views.generic.base import View
from rest_framework import generics, response, views
from taggit.models import Tag

from filetransfers.api import serve_file

from .serializers import LanguageSerializer


class TagList(views.APIView):
    """
    All tags in use on this system
    """

    def get(self, request, format=None):
        data = [tag.name for tag in Tag.objects.all()[:20]]
        return response.Response(data)


class LanguageList(generics.ListAPIView):
    serializer_class = LanguageSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        return self.model.objects.order_by('language_name').all()


class TagSearch(views.APIView):
    """
    Search tags in use on this system
    """

    def get(self, request, format=None, search=''):
        data = [tag.name for tag in Tag.objects.filter(name__startswith=search).all()[:20]]
        return response.Response(data)


# Non API views
# Download private documents based on content_type (id) and pk
# Only 'author' of a document is allowed
# TODO: Implement a real ACL for this

class DocumentDownloadView(View):
    def get(self, request, content_type, pk):
        type = ContentType.objects.get(pk=content_type)
        type_class = type.model_class()
        try:
            file = type_class.objects.get(pk=pk)
        except type_class.DoesNotExist:
            return HttpResponseNotFound()
        if file.author == request.user or request.user.is_staff:
            file_name = os.path.basename(file.file.name)
            return serve_file(request, file.file, save_as=file_name)
        return HttpResponseForbidden()


#TODO: this was creating problems with the tests
# TESTS
INCLUDE_TEST_MODELS = getattr(settings, 'INCLUDE_TEST_MODELS', False)

if INCLUDE_TEST_MODELS:
    from .models import MetaDataModel
    from .serializers import MetaDataSerializer


    class MetaDataDetail(generics.RetrieveAPIView):
        model = MetaDataModel
        serializer_class = MetaDataSerializer
