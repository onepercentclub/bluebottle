import datetime

from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from django.views.generic import FormView
from django import forms

from django.db.models import Sum, Count
from django.utils.datastructures import SortedDict
from bluebottle.payments.models import OrderPayment
from bluebottle.donations.models import Donation
from bluebottle.accounting.models import BankTransaction, RemoteDocdataPayment, RemoteDocdataPayout, BankTransactionCategory
from bluebottle.payouts.models import ProjectPayout

from .utils import get_accounting_statistics, get_dashboard_values
from .enum import BANK_ACCOUNTS

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


class AccountingOverviewView(FormView):
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


class AccountingDashboardView(FormView):
    template_name = 'admin/accounting/dashboard.html'
    form_class = PeriodForm

    def form_valid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_initial(self):
        initial = super(AccountingDashboardView, self).get_initial()
        today = datetime.date.today()
        self.selected_start = datetime.date(today.year, 1, 1)
        self.selected_stop = today
        initial['start'] = self.selected_start
        initial['stop'] = self.selected_stop
        return initial

    def get_context_data(self, **kwargs):
        form = kwargs.get('form')

        statistics = {}
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
