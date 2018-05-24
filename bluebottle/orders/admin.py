from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

from bluebottle.donations.admin import DonationInline
from bluebottle.orders.models import Order
from bluebottle.payments.services import PaymentService
from bluebottle.payments.admin import OrderPaymentInline
from bluebottle.utils.admin import TotalAmountAdminChangeList
from bluebottle.utils.utils import StatusDefinition


class OrderStatusFilter(SimpleListFilter):
    title = _('Status')

    parameter_name = 'status__exact'
    default_status = 'pending_or_success'

    def lookups(self, request, model_admin):
        choices = (('all', _('All')),
                   ('pending_or_success', _('Pending/Success')))
        return choices + Order.STATUS_CHOICES

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else
                lookup == self.default_status,
                'query_string': cl.get_query_string(
                    {self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() in dict(Order.STATUS_CHOICES):
            return queryset.filter(status=self.value())
        elif self.value() is None or self.value() == 'pending_or_success':
            return queryset.filter(status__in=[StatusDefinition.PENDING,
                                               StatusDefinition.SUCCESS])


class BaseOrderAdmin(admin.ModelAdmin):
    model = Order
    date_hierarchy = 'created'
    list_filter = (OrderStatusFilter, 'order_type')
    list_display = ('created', 'confirmed', 'completed', 'order_type', 'user',
                    'status', 'total')

    actions = ['reload_status']
    inlines = (DonationInline, OrderPaymentInline)

    search_fields = ('user__email',)

    raw_id_fields = ('user',)
    readonly_fields = ('status', 'total', 'created', 'confirmed', 'completed',
                       'order_type')

    def get_changelist(self, request, **kwargs):
        self.total_column = 'total'
        return TotalAmountAdminChangeList

    def reload_status(self, request, queryset):
        for order in queryset.all():
            for order_payment in order.order_payments.all():
                service = PaymentService(order_payment)
                service.check_payment_status()

    reload_status.short_description = _("Reload status from docdata")

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Order, BaseOrderAdmin)
