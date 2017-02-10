from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.core.urlresolvers import reverse
from django.db import connection
from django.http.response import HttpResponseRedirect
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from bluebottle.recurring_donations.models import MonthlyProject
from bluebottle.recurring_donations.tasks import prepare_monthly_batch, process_monthly_batch

from .models import (MonthlyDonation, MonthlyBatch, MonthlyOrder,
                     MonthlyDonor, MonthlyDonorProject)


class MonthlyProjectInline(admin.TabularInline):
    model = MonthlyProject
    readonly_fields = ('project', 'amount', 'fully_funded')
    fields = readonly_fields
    extra = 0
    can_delete = False
    ordering = ('-amount',)

    def has_add_permission(self, request):
        return False

    def fully_funded(self, obj):
        if obj.project.amount_needed <= obj.amount:
            return 'FUNDED'
        return '-'

    class Media:
        css = {"all": ("css/admin/hide_admin_original.css",)}


class MonthlyDonorProjectInline(admin.TabularInline):
    model = MonthlyDonorProject
    raw_id_fields = ('project',)
    fields = ('project',)
    extra = 0


class ActiveFilter(SimpleListFilter):
    title = _('Active')

    parameter_name = 'active__exact'
    active_choices = (('1', _('Yes')),
                      ('0', _('No')),)
    default = '1'

    def lookups(self, request, model_admin):
        return (('all', _('All')),) + self.active_choices

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else lookup == self.default,
                'query_string': cl.get_query_string(
                    {self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() in ('0', '1'):
            return queryset.filter(active=self.value())
        elif self.value() is None:
            return queryset.filter(active=self.default)


class MonthlyDonorAdmin(admin.ModelAdmin):
    model = MonthlyDonor
    list_display = ('user', 'amount', 'active', 'iban', 'selected_projects')
    raw_id_fields = ('user',)
    inlines = (MonthlyDonorProjectInline,)
    list_filter = (ActiveFilter,)
    search_fields = ('user__first_name', 'user__email', 'iban')

    def selected_projects(self, obj):
        return obj.projects.count() or '-'


admin.site.register(MonthlyDonor, MonthlyDonorAdmin)


class MonthlyDonorProjectAdmin(admin.ModelAdmin):
    model = MonthlyDonorProject
    list_display = ('donor', 'project')
    readonly_fields = ('donor',)
    raw_id_fields = ('project',)


admin.site.register(MonthlyDonorProject, MonthlyDonorProjectAdmin)


class MonthlyBatchAdmin(admin.ModelAdmin):
    model = MonthlyBatch
    readonly_fields = ('date', 'monthly_orders')
    inlines = (MonthlyProjectInline,)

    def monthly_orders(self, obj):
        url = '/admin/recurring_donations/monthlyorder/?processed__exact={0}&batch={1}'
        return format_html(
            u"<a href='{}'>{} processed</a><br/><a href='{}'>{1} unprocessed ({} errored)</a>",
            url.format(1, obj.id),
            obj.orders.filter(processed=True).count(),
            url.format(0, obj.id),
            obj.orders.filter(processed=False).count(),
            obj.orders.filter(error__gt='').count(),
        )

    def get_urls(self):
        urls = super(MonthlyBatchAdmin, self).get_urls()
        process_urls = [
            url(r'^prepare/$', self.prepare, name="recurring_donations_monthlybatch_prepare"),
            url(r'^process/(?P<pk>\d+)/$', self.process_batch, name="recurring_donations_monthlybatch_process")
        ]
        return process_urls + urls

    def process_batch(self, request, pk=None):
        batch = MonthlyBatch.objects.get(pk=pk)
        tenant = connection.tenant
        if getattr(settings, 'CELERY_RESULT_BACKEND', None):
            process_monthly_batch.delay(tenant=tenant, monthly_batch=batch, send_email=True)
        else:
            process_monthly_batch(tenant=tenant, monthly_batch=batch, send_email=True)
        batch_url = reverse('admin:recurring_donations_monthlybatch_change', args=(batch.id,))
        response = HttpResponseRedirect(batch_url)
        return response

    def prepare(self, request):
        batch = prepare_monthly_batch()
        batch_url = reverse('admin:recurring_donations_monthlybatch_change', args=(batch.id,))
        response = HttpResponseRedirect(batch_url)
        return response


admin.site.register(MonthlyBatch, MonthlyBatchAdmin)


class MonthlyDonationInline(admin.TabularInline):
    model = MonthlyDonation
    readonly_fields = ('amount',)
    raw_id_fields = ('project',)
    can_delete = False
    fields = ('project', 'amount')
    extra = 0

    def has_add_permission(self, request):
        return False


class MonthlyOrderAdmin(admin.ModelAdmin):
    model = MonthlyDonation
    list_display = ('user', 'amount', 'batch', 'processed', 'has_error')
    readonly_fields = ('user', 'amount', 'batch', 'iban', 'bic', 'name',
                       'city', 'processed', 'error_message')
    fields = readonly_fields
    list_filter = ('batch', 'processed')
    raw_id_fields = ('user', 'batch')
    inlines = (MonthlyDonationInline,)
    search_fields = ('user__email',)

    ordering = ('-batch', 'user__email')

    def error_message(self, obj):
        return format_html(
            u"<span style='color:red; font-weight: bold'>{}</span>",
            obj.error
        )

    def has_error(self, obj):
        if obj.error:
            return format_html(
                u"<span style='color:red; font-weight: bold'>ERROR!</span>"
            )
        return '-'


admin.site.register(MonthlyOrder, MonthlyOrderAdmin)


class MonthlyDonationAdmin(admin.ModelAdmin):
    model = MonthlyDonation
    list_display = ('user', 'project', 'order')
    raw_id_fields = ('user', 'project', 'order')


admin.site.register(MonthlyDonation, MonthlyDonationAdmin)
