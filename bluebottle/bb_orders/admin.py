from bluebottle.donations.admin import DonationInline
from bluebottle.payments.admin import OrderPaymentInline
from bluebottle.utils.admin import TotalAmountAdminChangeList
from bluebottle.utils.utils import StatusDefinition
from django.contrib import admin
from django.contrib.admin.filters import SimpleListFilter
from bluebottle.utils.model_dispatcher import get_order_model, get_donation_model
from django.utils.translation import ugettext_lazy as _


ORDER_MODEL = get_order_model()
DONATION_MODEL = get_donation_model()


class OrderStatusFilter(SimpleListFilter):
    title = _('Status')

    parameter_name = 'status__exact'
    default_status = 'pending_or_success'

    def lookups(self, request, model_admin):
        return (('all', _('All')), ('pending_or_success', _('Pending/Success')) ) + ORDER_MODEL.STATUS_CHOICES

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else lookup == self.default_status,
                'query_string': cl.get_query_string({self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() in dict(ORDER_MODEL.STATUS_CHOICES):
            return queryset.filter(status=self.value())
        elif self.value() is None or self.value() == 'pending_or_success':
            return queryset.filter(status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS])


class BaseOrderAdmin(admin.ModelAdmin):
    model = get_order_model()
    date_hierarchy = 'created'
    list_filter = (OrderStatusFilter, 'order_type')
    list_display = ('created', 'confirmed', 'completed', 'order_type', 'user', 'status', 'total')

    inlines = (DonationInline, OrderPaymentInline)

    search_fields = ('user__email', )

    raw_id_fields = ('user', )
    readonly_fields = ('status', 'total', 'created', 'confirmed', 'completed', 'order_type')

    def get_changelist(self, request):
        self.total_column = 'total'
        return TotalAmountAdminChangeList


admin.site.register(ORDER_MODEL, BaseOrderAdmin)

