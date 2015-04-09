from django import forms
from django.db import connection
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from .enum import BANK_ACCOUNTS
from .utils import get_accounting_statistics, get_dashboard_values, mydict

import datetime
from tenant_schemas.utils import get_tenant_model


class InitialDatesMixin(object):
    def get_initial(self):
        initial = super(InitialDatesMixin, self).get_initial()
        today = datetime.date.today()
        self.selected_start = datetime.date(today.year, 1, 1)
        self.selected_stop = today
        initial['start'] = self.selected_start
        initial['stop'] = self.selected_stop
        return initial


class PeriodForm(forms.Form):
    start = forms.DateField()
    stop = forms.DateField()

    def clean(self):
        cleaned_data = super(PeriodForm, self).clean()

        start = cleaned_data.get('start')
        stop = cleaned_data.get('stop')

        if start > stop:
            raise forms.ValidationError(_('Start date cannot be before stop date.'))

        return cleaned_data

    def get_start(self):
        start = self.cleaned_data['start']
        return timezone.datetime(start.year, start.month, start.day, 0, 0, 0, tzinfo=timezone.utc)

    def get_stop(self):
        stop = self.cleaned_data['stop']
        return timezone.datetime(stop.year, stop.month, stop.day, 12, 59, 59, tzinfo=timezone.utc)


class PeriodTenantForm(PeriodForm):
    tenant = forms.ModelChoiceField(queryset=get_tenant_model().objects.all(), empty_label=_('All tenants'), required=False)


class AccountingOverviewView(InitialDatesMixin, FormView):
    template_name = 'admin/accounting/overview.html'
    form_class = PeriodForm

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        form = kwargs.get('form')
        if form and form.is_valid():
            start = form.get_start()
            stop = form.get_stop()

            statistics = get_accounting_statistics(start, stop)
        else:
            statistics = {}

        context = super(AccountingOverviewView, self).get_context_data(**kwargs)
        context.update({
             'app_label': 'accounting',
             'title': _('Accountancy Overview'),
             'statistics': statistics,
        })
        return context


class AccountingDashboardView(InitialDatesMixin, FormView):
    template_name = 'admin/accounting/dashboard.html'
    form_class = PeriodForm

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        form = kwargs.get('form')

        if form and form.is_valid():
            self.selected_start = form.get_start()
            self.selected_stop = form.get_stop()

        statistics = get_accounting_statistics(self.selected_start, self.selected_stop)
        data = get_dashboard_values(self.selected_start, self.selected_stop)

        context = super(AccountingDashboardView, self).get_context_data(**kwargs)
        context.update({
             'app_label': 'accounting',
             'title': _('Finance Dashboard'),
             'statistics': statistics,
             'data': data,
             'start': self.selected_start,
             'stop': self.selected_stop,
             'bank_accounts': BANK_ACCOUNTS
        })
        return context


class MultiTenantAccountingOverviewView(InitialDatesMixin, FormView):
    """
    Same as AccountingOverviewView but context data will contain
    totals for all tenants (or just one).

    Could subclass from other view, but make sure there is no way
    that the 'normal' AccountingOverviewView can contain data for multiple tenants.
    """
    template_name = 'admin/accounting/overview.html'
    form_class = PeriodTenantForm

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        form = kwargs.get('form')

        if form and form.is_valid():
            start = form.get_start()
            stop = form.get_stop()
            tenant = form.cleaned_data.get('tenant', None)

            if tenant:
                connection.set_tenant(tenant)
                header = ' - {}'.format(tenant.name)
                statistics = get_accounting_statistics(start, stop)
            else:
                header = ' - All tenants'
                statistics = mydict()

                for tenant in get_tenant_model().objects.all():
                    connection.set_tenant(tenant)
                    statistics += get_accounting_statistics(start, stop)
        else:
            header = ''
            statistics = {}

        context = super(MultiTenantAccountingOverviewView, self).get_context_data(**kwargs)

        context.update({
             'app_label': 'accounting',
             'title': _('Accountancy Overview') + header,
             'statistics': statistics,
        })
        return context


class MultiTenantAccountingDashboardView(InitialDatesMixin, FormView):
    """
    Same as AccountingDashboardView, but for multiple tenants.
    Could be subclassed, but the distinction should be very clear,
    this view can contain data from all tenants, the other view can NOT.
    """
    template_name = 'admin/accounting/dashboard.html'
    #template_name = 'admin/accounting/multiadmin/multi_tenant_dashboard.html'
    form_class = PeriodTenantForm

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        """
        Get the statistics data for the selected tenant, or for all tenants.
        In the last case, the connection will be switched for each tenant,
        and the data for each tenant will be added to the total.
        """
        form = kwargs.get('form')

        all_tenants = None

        if form and form.is_valid():
            self.selected_start = form.get_start()
            self.selected_stop = form.get_stop()
            tenant = form.cleaned_data.get('tenant', None)

            if tenant:
                connection.set_tenant(tenant)
                statistics = get_accounting_statistics(self.selected_start, self.selected_stop)
                totals = get_dashboard_values(self.selected_start, self.selected_stop)

                header = ' - {}'.format(tenant.name)
            else:
                header = ' - All tenants'
                statistics = mydict()
                totals = mydict()
                all_tenants = {}  # contains data for each tenant when all are selected

                for tenant in get_tenant_model().objects.all():
                    connection.set_tenant(tenant)

                    stats = get_accounting_statistics(self.selected_start, self.selected_stop)
                    tots = get_dashboard_values(self.selected_start, self.selected_stop)

                    statistics += stats
                    totals += tots

                    all_tenants[tenant.name] = {
                        'statistics': stats,
                        'totals': tots,
                        }
        else:
            header = ''
            statistics, totals = {}, {}

        context = super(MultiTenantAccountingDashboardView, self).get_context_data(**kwargs)

        context.update({
             'statistics': statistics,
             'all_tenants': all_tenants,  # is None in all cases when not 'all tenants' are selected in the multi admin view
             'data': totals,
             'app_label': 'accounting',
             'title': _('Finance Dashboard') + header,
             'start': self.selected_start,
             'stop': self.selected_stop,
             'bank_accounts': BANK_ACCOUNTS
        })

        return context
