import mimetypes
import os
from io import BytesIO
from operator import attrgetter

import icalendar
import magic
import xlsxwriter
from django.core.paginator import Paginator
from django.core.signing import TimestampSigner, BadSignature
from django.db.models import Case, When, IntegerField
from django.http import Http404, HttpResponse
from django.utils import translation
from django.utils.functional import cached_property
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from parler.utils.i18n import get_language
from rest_framework import generics
from rest_framework import views, response
from rest_framework.pagination import PageNumberPagination
from rest_framework_json_api.exceptions import exception_handler
from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework_json_api.parsers import JSONParser
from rest_framework_json_api.views import AutoPrefetchMixin
from rest_framework_jwt.authentication import JSONWebTokenAuthentication
from taggit.models import Tag

from bluebottle.bluebottle_drf2.renderers import BluebottleJSONAPIRenderer
from bluebottle.clients import properties
from bluebottle.utils.admin import prep_field
from bluebottle.utils.permissions import ResourcePermission
from .models import Language
from .serializers import LanguageSerializer

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


class ModelTranslationViewMixin():
    def get(self, request, *args, **kwargs):
        language = request.query_params.get('language', properties.LANGUAGE_CODE)
        translation.activate(language)
        return super(ModelTranslationViewMixin, self).get(request, *args, **kwargs)


class ViewPermissionsMixin():
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


class RelatedPermissionMixin():
    related_permission_classes = {}

    def check_object_permissions(self, request, obj):
        self.check_related_object_permissions(request, obj)
        super(RelatedPermissionMixin, self).check_object_permissions(
            request, obj
        )

    def check_related_object_permissions(self, request, obj):
        """
        Check if the request should be permitted for a given related object.
        Raises an appropriate exception if the request is not permitted.
        """
        for related, permissions in list(self.related_permission_classes.items()):
            related_obj = attrgetter(related)(obj)
            for permission in permissions:
                if not permission().has_object_permission(request, None, related_obj):
                    self.permission_denied(
                        request, message=getattr(permission, 'message', None)
                    )


class ListCreateAPIView(RelatedPermissionMixin, ViewPermissionsMixin, generics.ListCreateAPIView):
    permission_classes = (ResourcePermission,)

    def perform_create(self, serializer):
        self.check_object_permissions(
            self.request,
            serializer.Meta.model(**serializer.validated_data)
        )

        serializer.save()


class CreateAPIView(RelatedPermissionMixin, ViewPermissionsMixin, generics.CreateAPIView):
    permission_classes = (ResourcePermission,)

    def perform_create(self, serializer):
        if hasattr(serializer.Meta, 'model'):
            self.check_object_permissions(
                self.request,
                serializer.Meta.model(**serializer.validated_data)
            )
        serializer.save()


class RetrieveUpdateAPIView(
    RelatedPermissionMixin, ViewPermissionsMixin, generics.RetrieveUpdateAPIView
):
    base_permission_classes = (ResourcePermission,)


class RetrieveUpdateDestroyAPIView(
    RelatedPermissionMixin, ViewPermissionsMixin, generics.RetrieveUpdateDestroyAPIView
):
    base_permission_classes = (ResourcePermission,)


class PrivateFileView(DetailView):
    """ Serve private files using X-sendfile header. """
    field = None  # Field on the model that is the actual file
    relation = None  # If the file is in a related object (e.g. Document)
    signer = TimestampSigner()
    max_age = 6 * 60 * 60  # 6 hours
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
        if self.relation:
            field = getattr(getattr(self.get_object(), self.relation), self.field)
        else:
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
        qs = super(TranslatedApiViewMixin, self).get_queryset().translated(
            get_language()
        )
        qs = qs.order_by(*qs.model._meta.ordering)
        return qs


class ESPaginator(Paginator):
    @cached_property
    def count(self):
        """
        Returns the total number of objects, across all pages.
        """
        if isinstance(self.object_list, tuple):
            _, object_list = self.object_list
        else:
            object_list = self.object_list

        try:
            return object_list.count()
        except (AttributeError, TypeError):
            # AttributeError if object_list has no count() method.
            # TypeError if object_list.count() requires arguments
            # (i.e. is of type list).
            return len(object_list)

    def page(self, number):
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page

        if top + self.orphans >= self.count:
            top = self.count

        if isinstance(self.object_list, tuple):
            queryset, search = self.object_list
            page = self._get_page(search[bottom:top], number, self)

            try:
                pks = [result.meta.id for result in search[bottom:top].execute()]
                queryset = queryset.filter(pk__in=pks)
            except ValueError:
                pks = search.to_queryset().values_list('id', flat=True)
                queryset = search.to_queryset()

            preserved_order = Case(
                *[When(pk=pk, then=pos) for pos, pk in enumerate(pks)],
                output_field=IntegerField()
            )
            page.object_list = queryset.annotate(search_order=preserved_order).order_by('search_order')
        else:
            page = self._get_page(self.object_list[bottom:top], number, self)

        return page


class JsonApiPagination(JsonApiPageNumberPagination):
    page_size = 8
    max_page_size = None
    django_paginator_class = ESPaginator


class JsonApiViewMixin(AutoPrefetchMixin):

    pagination_class = JsonApiPagination
    parser_classes = (JSONParser,)
    renderer_classes = (BluebottleJSONAPIRenderer,)

    authentication_classes = (JSONWebTokenAuthentication,)

    def get_exception_handler(self):
        return exception_handler


class NoPagination(PageNumberPagination):
    page_size = 10000


class IcalView(PrivateFileView):
    max_age = 30 * 60  # half an hour

    @property
    def details(self):
        return self.get_object().description

    def get(self, *args, **kwargs):
        instance = self.get_object()
        calendar = icalendar.Calendar()

        event = icalendar.Event()
        event.add('summary', instance.title)
        event.add('description', self.details)
        event.add('url', instance.get_absolute_url())
        event.add('dtstart', instance.start)
        event.add('dtend', instance.end)
        event['uid'] = instance.uid

        organizer = icalendar.vCalAddress('MAILTO:{}'.format(instance.owner.email))
        organizer.params['cn'] = icalendar.vText(instance.owner.full_name)

        event['organizer'] = organizer
        if instance.location:
            event['location'] = icalendar.vText(instance.location.formatted_address)

        calendar.add_component(event)

        response = HttpResponse(calendar.to_ical(), content_type='text/calendar')
        response['Content-Disposition'] = 'attachment; filename="%s.ics"' % (
            instance.slug
        )

        return response


class ExportView(PrivateFileView):
    filename = 'exports'

    def get_fields(self):
        return self.fields

    def get_filename(self):
        return f'{self.filename} for {self.get_object()}.xlsx'

    def get_row(self, instance):
        return [prep_field(self.request, instance, field[0]) for field in self.get_fields()]

    def get_data(self):
        return [self.get_row(instance) for instance in self.get_instances()]

    def get_instances(self):
        raise NotImplementedError()

    def write_data(self, workbook):
        worksheet = workbook.add_worksheet(str(self.get_object())[:30])

        worksheet.write_row(0, 0, [field[1] for field in self.get_fields()])

        for (index, row) in enumerate(self.get_data()):
            worksheet.write_row(index + 1, 0, row)

    def get(self, request, *args, **kwargs):
        output = BytesIO()

        workbook = xlsxwriter.Workbook(output, {'remove_timezone': True})
        self.write_data(workbook)
        workbook.close()

        output.seek(0)

        response = HttpResponse(output.read())

        response['Content-Disposition'] = f'attachment; filename="{self.get_filename()}"'
        response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        return response
