import re
from datetime import datetime
import pendulum

from django import forms
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View, TemplateView
from django.views.generic.edit import FormView

from bluebottle.analytics.reports import MetricsReport
from .tasks import generate_participation_metrics


class ParticipationMetricsForm(forms.Form):
    CURRENT_YEAR = datetime.now().year
    START_YEAR_CHOICES = ((year, '{}'.format(year)) for year in range(CURRENT_YEAR - 3, CURRENT_YEAR + 1))
    END_YEAR_CHOICES = ((year, '{}'.format(year)) for year in range(CURRENT_YEAR - 3, CURRENT_YEAR + 1))

    email = forms.EmailField(disabled=True, required=True)
    start_year = forms.ChoiceField(choices=START_YEAR_CHOICES,
                                   initial=CURRENT_YEAR - 3,
                                   label=_('Start Year'),
                                   required=True)
    end_year = forms.ChoiceField(choices=END_YEAR_CHOICES, initial=CURRENT_YEAR, label=_('End Year'), required=True)

    def clean(self):
        cleaned_data = super(ParticipationMetricsForm, self).clean()
        start_year = cleaned_data.get("start_year")
        end_year = cleaned_data.get("end_year")

        if start_year > end_year:
            raise forms.ValidationError(_('Start year cannot be greater than the End year'), code='invalid')

    def generate_metrics(self):
        email = self.cleaned_data['email']
        start_year = self.cleaned_data['start_year']
        end_year = self.cleaned_data['end_year']
        tenant = connection.tenant.client_name
        generate_participation_metrics.delay(tenant, email, start_year, end_year)


class ParticipationMetricsFormView(FormView):
    form_class = ParticipationMetricsForm
    template_name = 'participation_metrics.html'

    def get_success_url(self):
        return reverse('participation-metrics')

    def get_initial(self):
        initial = super(ParticipationMetricsFormView, self).get_initial()
        initial['email'] = self.request.user
        return initial

    def form_valid(self, form):
        now = pendulum.now()
        twenty_four_hours_ago = pendulum.now().subtract(hours=4)
        participation_metrics_request_datetime = self.request.session.get('participation_metrics_request_datetime', 0)

        if pendulum.from_timestamp(participation_metrics_request_datetime).between(now, twenty_four_hours_ago):
            messages.add_message(self.request, messages.WARNING,
                                 _('Sorry! You can request the participation metrics report once in 24 hours.'))
        else:
            self.request.session['participation_metrics_request_datetime'] = now.int_timestamp
            form.generate_metrics()
            messages.add_message(self.request, messages.INFO,
                                 _('The participation metrics report will be emailed to you in a couple of hours'))
        return super(ParticipationMetricsFormView, self).form_valid(form)


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
        response['Content-Disposition'] = "attachment; filename={}".format(filename)

        return response
