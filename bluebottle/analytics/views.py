import re

from django.db import connection
from django.http import HttpResponse
from django.utils.timezone import now
from django.views.generic.base import View, TemplateView

from bluebottle.analytics.reports import MetricsReport


class ReportExportView(TemplateView):
    template_name = 'report_export.html'


class ReportDownloadView(View):
    def get(self, request, *args, **kwargs):
        client_name = re.sub(r'\s+', '_', connection.tenant.name)
        dt_now = now().strftime('%d-%m-%Y_%H-%M-%S')
        filename = "Report-{}-{}.xlsx".format(client_name, dt_now)

        report = MetricsReport()
        output = report.to_output()
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

        return response
