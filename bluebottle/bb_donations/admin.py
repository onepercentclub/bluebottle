from babel.numbers import format_currency
from bluebottle.utils.utils import get_model_class
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.templatetags.admin_static import static
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

DONATION_MODEL = get_model_class('DONATIONS_DONATION_MODEL')


# http://stackoverflow.com/a/16556771
class DonationStatusFilter(SimpleListFilter):
    title = _('Status')

    parameter_name = 'status__exact'
    default_status = DONATION_MODEL.DonationStatuses.paid

    def lookups(self, request, model_admin):
        return (('all', _('All')),) + DONATION_MODEL.DonationStatuses.choices

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else lookup == self.default_status,
                'query_string': cl.get_query_string({self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() in DONATION_MODEL.DonationStatuses.values:
            return queryset.filter(status=self.value())
        elif self.value() is None:
            return queryset.filter(status=self.default_status)


payment_method_icon_mapping = {
    'iDeal': 'fund/icon-ideal.svg',
    'Direct debit': 'fund/icon-direct-debit.png',
    'Mastercard': 'fund/icon-mastercard.svg',
    'Visa': 'fund/icon-visa.svg',
    'Gift Card': 'fund/icon-gift-card.svg',
}



class DonationAdmin(admin.ModelAdmin):
    date_hierarchy = 'updated'
    list_display = ('updated', 'project', 'user', 'amount', 'status')
    list_filter = (DonationStatusFilter, )
    ordering = ('-updated', )
    raw_id_fields = ('user', 'project', 'fundraiser')
    readonly_fields = ('view_order', 'created', 'updated')
    fields = readonly_fields + ('status', 'amount', 'user', 'project', 'fundraiser')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'project__title')

    def view_order(self, obj):
        url = reverse('admin:%s_%s_change' % (obj.order._meta.app_label, obj.order._meta.module_name), args=[obj.order.id])
        return "<a href='%s'>View Order</a>" % (str(url))

    view_order.allow_tags = True

admin.site.register(DONATION_MODEL, DonationAdmin)
