import mimetypes
import os
from collections import namedtuple

import magic
from django.conf import settings
from django.core.paginator import Paginator
from django.core.signing import TimestampSigner, BadSignature
from django.http import Http404, HttpResponse
from django.http.response import HttpResponseNotFound
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django_elasticsearch_dsl.search import Search
from parler.utils.i18n import get_language
from rest_framework import generics
from rest_framework import views, response
from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from sorl.thumbnail.shortcuts import get_thumbnail
from taggit.models import Tag
from tenant_extras.utils import TenantLanguage

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.clients import properties
from bluebottle.projects.models import Project
from bluebottle.utils.email_backend import send_mail
from bluebottle.utils.permissions import ResourcePermission
from .models import Language
from .serializers import ShareSerializer, LanguageSerializer

mime = magic.Magic(mime=True)


class TagList(views.APIView):
    """ All tags in use on this system """

    def get(self, request, format=None):
        data = [tag.name for tag in Tag.objects.all()[:20]]
        return response.Response(data)


class LanguageList(generics.ListAPIView):
    serializer_class = LanguageSerializer
    queryset = Language.objects.all()

    def get_queryset(self):
        return Language.objects.order_by('language_name').all()


class TagSearch(views.APIView):
    """ Search tags in use on this system """

    def get(self, request, format=None, search=''):
        data = [tag.name for tag in
                Tag.objects.filter(name__startswith=search).all()[:20]]
        return response.Response(data)


class ShareFlyer(views.APIView):
    serializer_class = ShareSerializer

    def project_args(self, projectid):
        try:
            project = Project.objects.get(slug=projectid)
        except Project.DoesNotExist:
            return None

        if project.image:
            project_image = self.request.build_absolute_uri(
                settings.MEDIA_URL + unicode(get_thumbnail(project.image,
                                                           "400x225",
                                                           crop="center")))
        else:
            project_image = None

        args = dict(
            project_title=project.title,
            project_pitch=project.pitch,
            project_image=project_image
        )

        return args

    def get(self, request, *args, **kwargs):
        """ Return the bare email as preview. We do not have access to the
        logged in user so use fake data
        """

        data = request.GET

        args = self.project_args(data.get('project'))

        if args is None:
            return HttpResponseNotFound()

        args['share_name'] = "John Doe"
        args['share_email'] = "john@example.com"

        if self.request.user.is_authenticated():
            args[
                'sender_name'] = self.request.user.get_full_name() or self.request.user.username
            args['sender_email'] = self.request.user.email
        else:
            args['sender_name'] = "John Doe"
            args['sender_email'] = "john.doe@example.com"

        args['share_motivation'] = """
        (sample motivation) Great to see you again this afternoon.
        Attached you'll find a project flyer for the big event next friday.
        If you care to join in, please let me know,
        I'll add you as my +1 on the attendee list.
        Hope to hear from you soon
        Cheers,
        Jane"""
        result = render_to_string('utils/mails/share_flyer.mail.html', args)
        return response.Response({'preview': result})

    def post(self, request, *args, **kwargs):
        serializer = ShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        args = self.project_args(serializer.validated_data.get('project'))
        if args is None:
            return HttpResponseNotFound()

        sender_name = self.request.user.get_full_name() or self.request.user.username
        sender_email = self.request.user.email
        share_name = serializer.validated_data.get('share_name', None)
        share_email = serializer.validated_data.get('share_email', None)
        share_motivation = serializer.validated_data.get('share_motivation', None)
        share_cc = serializer.validated_data.get('share_cc')

        with TenantLanguage(self.request.user.primary_language):
            subject = _('%(name)s wants to share a project with you!') % dict(
                name=sender_name)

        args.update(dict(
            template_name='utils/mails/share_flyer.mail',
            subject=subject,
            to=namedtuple("Receiver", "email")(email=share_email),
            share_name=share_name,
            share_email=share_email,
            share_motivation=share_motivation,
            sender_name=sender_name,
            sender_email=sender_email,
            reply_to=sender_email,
            cc=[sender_email] if share_cc else []
        ))
        if share_cc:
            args['cc'] = [sender_email]

        send_mail(**args)

        return response.Response({}, status=201)


class ModelTranslationViewMixin(object):
    def get(self, request, *args, **kwargs):
        language = request.query_params.get('language', properties.LANGUAGE_CODE)
        translation.activate(language)
        return super(ModelTranslationViewMixin, self).get(request, *args, **kwargs)


class ViewPermissionsMixin(object):
    """ View mixin with permission checks added from the DRF APIView """
    @property
    def model(self):
        model_cls = None
        try:
            if hasattr(self, 'queryset'):
                model_cls = self.queryset.model
            elif hasattr(self, 'get_queryset'):
                model_cls = self.get_queryset().model
        except AttributeError:
            pass

        return model_cls


class LoginWithView(TemplateView):

    template_name = 'utils/login_with.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


class PermissionedView(View, ViewPermissionsMixin):
    pass


class GenericAPIView(ViewPermissionsMixin, generics.GenericAPIView):
    permission_classes = (ResourcePermission,)


class ListAPIView(ViewPermissionsMixin, generics.ListAPIView):
    permission_classes = (ResourcePermission,)


class UpdateAPIView(ViewPermissionsMixin, generics.UpdateAPIView):
    permission_classes = (ResourcePermission,)


class RetrieveAPIView(ViewPermissionsMixin, generics.RetrieveAPIView):
    permission_classes = (ResourcePermission,)


class ListCreateAPIView(ViewPermissionsMixin, generics.ListCreateAPIView):
    permission_classes = (ResourcePermission,)

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save()


class RelatedPermissionMixin(object):
    related_permission_classes = {}

    def check_related_object_permissions(self, request, obj):
        """
        Check if the request should be permitted for a given related object.
        Raises an appropriate exception if the request is not permitted.
        """
        for related, permissions in self.related_permission_classes.items():
            related_obj = getattr(obj, related)
            for permission in permissions:
                if not permission().has_object_permission(request, None, related_obj):
                    self.permission_denied(
                        request, message=getattr(permission, 'message', None)
                    )


class CreateAPIView(ViewPermissionsMixin, generics.CreateAPIView, RelatedPermissionMixin):
    permission_classes = (ResourcePermission,)

    def perform_create(self, serializer):
        if hasattr(serializer.Meta, 'model'):
            self.check_object_permissions(
                self.request,
                serializer.Meta.model(**serializer.validated_data)
            )
            self.check_related_object_permissions(
                self.request,
                serializer.Meta.model(**serializer.validated_data)
            )
        serializer.save()


class RetrieveUpdateAPIView(ViewPermissionsMixin, generics.RetrieveUpdateAPIView):
    base_permission_classes = (ResourcePermission,)


class RetrieveUpdateDestroyAPIView(ViewPermissionsMixin, generics.RetrieveUpdateDestroyAPIView):
    base_permission_classes = (ResourcePermission,)


class PrivateFileView(DetailView):
    """ Serve private files using X-sendfile header. """
    field = None  # Field on the model that is the actual file
    signer = TimestampSigner()
    max_age = 6 * 60 * 60
    query_pk_and_slug = True

    def get_object(self):
        try:
            url = self.signer.unsign(self.request.GET['signature'], max_age=self.max_age)
        except (KeyError, BadSignature):
            raise Http404()

        if not url == self.request.path:
            raise Http404()

        return super(PrivateFileView, self).get_object()

    def get(self, request, *args, **kwargs):
        field = getattr(self.get_object(), self.field)
        filename = os.path.basename(field.name)
        content_type = mimetypes.guess_type(filename)[0]
        response = HttpResponse()
        response['X-Accel-Redirect'] = field.url
        response['Content-Type'] = content_type
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            field.name
        )
        try:
            response['Content-Type'] = mime.from_file(field.path)
        except IOError:
            pass

        return response


class OwnerListViewMixin(object):
    def get_queryset(self):
        qs = super(OwnerListViewMixin, self).get_queryset()

        model = super(OwnerListViewMixin, self).model
        permission = '{}.api_read_{}'.format(
            model._meta.app_label, model._meta.model_name
        )

        if not self.request.user.has_perm(permission):
            user = self.request.user if self.request.user.is_authenticated else None
            qs = qs.filter(**{self.owner_filter_field: user})

        return qs


class TranslatedApiViewMixin(object):
    def get_queryset(self):
        qs = super(TranslatedApiViewMixin, self).get_queryset().language(
            get_language()
        )
        qs = qs.order_by(*qs.model._meta.ordering)
        return qs


class ESPaginator(Paginator):
    def page(self, *args, **kwargs):
        page = super(ESPaginator, self).page(*args, **kwargs)

        if isinstance(page.object_list, Search):
            page.object_list = page.object_list.to_queryset()
        return page


class JsonApiPagination(JsonApiPageNumberPagination):
    page_size = 8
    django_paginator_class = ESPaginator


class JsonApiViewMixin(AutoPrefetchMixin):

    pagination_class = JsonApiPagination

    parser_classes = (JSONParser,)
    renderer_classes = (BluebottleJSONAPIRenderer,)

    authentication_classes = (JSONWebTokenAuthentication,)
