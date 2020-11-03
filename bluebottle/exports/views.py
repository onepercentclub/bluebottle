from builtins import object
import json
import posixpath

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.db import connection
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.urls.base import reverse
from django.views.generic import FormView, View
from django.views.decorators.csrf import csrf_protect

from django.views.generic.detail import DetailView

import rules
from celery.result import AsyncResult

from bluebottle.exports.tasks import plain_export

from .compat import import_string, jquery_in_vendor
from .exporter import get_export_models, Exporter
from .tasks import export


EXPORTDB_EXPORT_KEY = 'exportdb_export'


class ExportPermissionMixin(object):
    """
    Check permissions
    """
    @method_decorator(staff_member_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        if not rules.test_rule('exportdb.can_export', request.user):
            raise PermissionDenied
        return super(ExportPermissionMixin, self).dispatch(request, *args, **kwargs)


class ExportView(ExportPermissionMixin, FormView):
    form_class = None
    template_name = 'exportdb/confirm.html'
    exporter_class = Exporter

    def get_form_class(self):
        """
        Return the form class to use for the confirmation form.

        In the method instead of the attribute, since it's not guaranteed that
        the appconf is loaded in Django versions < 1.7.
        """
        if self.form_class is None:
            self.form_class = import_string(settings.EXPORTDB_CONFIRM_FORM)
        return self.form_class

    def get_export_models(self, **kwargs):
        kwargs.setdefault('admin_only', False)
        try:
            return get_export_models(**kwargs)
        except ImproperlyConfigured as e:
            messages.error(self.request, e.args[0])
        return []

    def get_exporter_class(self):
        return self.exporter_class

    def get_context_data(self, **kwargs):
        context = super(ExportView, self).get_context_data(**kwargs)
        context['title'] = _('Export database')
        context['jquery_in_vendor'] = jquery_in_vendor()
        context['models'] = [
            u'{name} ({app}.{model})'.format(
                name=model._meta.verbose_name,
                app=model._meta.app_label,
                model=model.__name__
            )
            for model in self.get_export_models()
        ]
        return context

    def form_valid(self, form):
        # multi-tenant support
        tenant = getattr(connection, 'tenant', None)
        # start actual export and render the template
        if settings.EXPORTDB_USE_CELERY:
            async_result = export.delay(self.get_exporter_class(), tenant=tenant, **form.cleaned_data)
            self.request.session[EXPORTDB_EXPORT_KEY] = async_result.id
            context = self.get_context_data(export_running=True)
            self.template_name = 'exportdb/in_progress.html'
            return self.render_to_response(context)
        else:
            result = plain_export(self.get_exporter_class(), tenant=tenant, **form.cleaned_data)
            filename = result.split('/')[-1]
            output = open(result, 'r')
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            return response


class ExportPendingView(ExportPermissionMixin, View):

    def json_response(self, data):
        return HttpResponse(json.dumps(data), content_type='application/json')

    def get(self, request, *args, **kwargs):
        async_result = AsyncResult(request.session.get(EXPORTDB_EXPORT_KEY))
        if not async_result:
            return self.json_response({'status': 'FAILURE', 'progress': 0})

        if async_result.state == 'PROGRESS':
            progress = async_result.info['progress']
            if progress > 0.99:
                progress = 0.99
        elif async_result.ready():
            progress = 1
        else:
            progress = 1

        content = {
            'status': async_result.state,
            'progress': progress,
            'file': reverse('exportdb_download', args=(async_result.result, )) if async_result.ready() else None
        }
        return self.json_response(content)


class ExportDownloadView(ExportPermissionMixin, DetailView):
    """ Serve private files using X-sendfile header. """

    def get(self, request, filename):
        response = HttpResponse()

        response['X-Accel-Redirect'] = posixpath.join(settings.EXPORTDB_EXPORT_MEDIA_URL, filename)
        response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(
            filename
        )

        return response
