from django.conf import settings
import os

from django.contrib.contenttypes.models import ContentType
from django.http.response import HttpResponseForbidden, HttpResponseNotFound
from django.views.generic.base import View

from filetransfers.api import serve_file
from rest_framework import generics
from rest_framework import views, response
from taggit.models import Tag

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

from bluebottle.utils.email_backend import send_mail
from django.utils.translation import ugettext as _
from collections import namedtuple
from django.http import HttpResponse
from bluebottle.utils.model_dispatcher import get_project_model
from sorl.thumbnail.shortcuts import get_thumbnail
from django.template.loader import render_to_string
from django.template import Context

PROJECT_MODEL = get_project_model()

class ShareFlyerView(View):
    def project_args(self, projectid):
        try:
            project = PROJECT_MODEL.objects.get(slug=projectid)
        except PROJECT_MODEL.DoesNotExist:
            return None

        project_image = self.request.build_absolute_uri(settings.MEDIA_URL + unicode(get_thumbnail(project.image, "400x380")))
        args = dict(
            project_title=project.title,
            project_pitch=project.pitch,
            project_image=project_image
        )

        return args

    def get(self, request, *args, **kwargs):
        """
            return the bare email as preview. We do not have access to the
            logged in user so use fake data
        """
        data = request.GET

        args = self.project_args(data.get('projectid'))

        if args is None:
            return HttpResponseNotFound()

        args['share_name'] = "John Doe"
        args['share_email'] = "john@example.com"
        args['sender_name'] = "Jane Doe"
        args['sender_email'] = "jane@example.com"

        args['share_motivation'] = """(sample motivation) Great to see you again this afternoon. Attached you'll find a project flyer for the big event next friday. If you care to join in, please let me know, I'll add you as my +1 on the attendee list.

        Hope to hear from you soon

        Cheers,

        Jane"""
        result = render_to_string('utils/mails/share_flyer.mail.html', {}, Context(args))
        return HttpResponse(result, status=200)

    def post(self, request, *args, **kwargs):
        data = request.POST

        args = self.project_args(data.get('projectid'))
        if args is None:
            return HttpResponseNotFound()

        sender_name = self.request.user.get_full_name() or self.request.user.username
        sender_email = self.request.user.email
        share_name = data.get('share_name', None)
        share_email = data.get('share_email', None)
        share_motivation = data.get('share_motivation', None)
        share_cc = data.get('share_cc', False) 

        args.update(dict(
            template_name='utils/mails/share_flyer.mail',
            subject=_('%(name)s wants to share a project with you!') % dict(name=sender_name),
            to=namedtuple("Receiver", "email")(email=share_email),
            from_email=sender_email,
            share_name=share_name,
            share_email=share_email,
            share_motivation=share_motivation,
            sender_name=sender_name,
            sender_email=sender_email,
        ))
        if share_cc:
            args['cc'] = [sender_email]

        result = send_mail(**args)

        return HttpResponse(result, status=200)

#TODO: this was creating problems with the tests
# TESTS
INCLUDE_TEST_MODELS = getattr(settings, 'INCLUDE_TEST_MODELS', False)

if INCLUDE_TEST_MODELS:
    from .models import MetaDataModel
    from .serializers import MetaDataSerializer


    class MetaDataDetail(generics.RetrieveAPIView):
        model = MetaDataModel
        serializer_class = MetaDataSerializer
