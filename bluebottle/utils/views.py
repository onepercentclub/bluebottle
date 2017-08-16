from collections import namedtuple

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponseForbidden, HttpResponseNotFound, HttpResponse
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.utils import translation
from django.views.generic.base import View

from rest_framework import generics
from rest_framework import views, response
from sorl.thumbnail.shortcuts import get_thumbnail
from taggit.models import Tag
from tenant_extras.utils import TenantLanguage

from bluebottle.clients import properties
from bluebottle.projects.models import Project
from bluebottle.utils.email_backend import send_mail
from bluebottle.utils.permissions import ResourcePermissions

from .models import Language
from .serializers import ShareSerializer, LanguageSerializer


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

    base_permission_classes = ()

    def get_permissions(self):
        """ Combine and return the base_permission_classes appended to the standard
        permission_classes
        """

        all_permission_classes = (tuple(self.permission_classes) +
                                  self.base_permission_classes)
        return [permission() for permission in all_permission_classes]

    def check_permissions(self, request):
        """ Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """

        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

    def check_object_permissions(self, request, obj):
        """ Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """

        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )

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


class PermissionedView(View, ViewPermissionsMixin):
    def dispatch(self, request, *args, **kwargs):
        view = super(PermissionedView, self).dispatch(request, *args, **kwargs)

        # FIXME: The request object below does not have the session authenticated user
        #        so the permission check does not work!
        self.check_permissions(request)

        return view

    def permission_denied(self, request, message):
        raise PermissionDenied()

    def check_permission(self, request, instance):

        # Permission check should happen in the permission_classes
        return True


class PrivateFileView(PermissionedView):
    """ Serve private files using X-sendfile header. """

    queryset = None  # Queryset that is used for finding ojects
    field = None  # Field on the model that is the actual file

    def get(self, request, pk):
        try:
            instance = self.queryset.get(pk=pk)
        except self.queryset.DoesNotExist:
            return HttpResponseNotFound()

        try:
            self.check_object_permissions(request, instance)
        except PermissionDenied:
            return HttpResponseForbidden()

        field = getattr(instance, self.field)
        response = HttpResponse()
        response['X-Accel-Redirect'] = field.url
        response['Content-Disposition'] = 'attachment; filename={}'.format(
            field.name
        )

        return response


class GenericAPIView(ViewPermissionsMixin, generics.GenericAPIView):
    base_permission_classes = (ResourcePermissions,)


class ListAPIView(ViewPermissionsMixin, generics.ListAPIView):
    base_permission_classes = (ResourcePermissions,)


class UpdateAPIView(ViewPermissionsMixin, generics.UpdateAPIView):
    base_permission_classes = (ResourcePermissions,)


class RetrieveAPIView(ViewPermissionsMixin, generics.RetrieveAPIView):
    base_permission_classes = (ResourcePermissions,)


class ListCreateAPIView(ViewPermissionsMixin, generics.ListCreateAPIView):
    base_permission_classes = (ResourcePermissions,)


class RetrieveUpdateAPIView(ViewPermissionsMixin, generics.RetrieveUpdateAPIView):
    base_permission_classes = (ResourcePermissions,)


class RetrieveUpdateDestroyAPIView(ViewPermissionsMixin, generics.RetrieveUpdateDestroyAPIView):
    base_permission_classes = (ResourcePermissions,)
