from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html

from bluebottle.payments_logger.models import PaymentLogEntry


class PaymentLogEntryInline(admin.TabularInline):
    model = PaymentLogEntry
    readonly_fields = ('timestamp', 'message', 'level')
    fields = readonly_fields
    extra = 0
    can_delete = False
    ordering = ('-timestamp',)

    def has_add_permission(self, request):
        return False

    class Media:
        css = {"all": ("css/admin/hide_admin_original.css",)}


class PaymentLogEntryAdmin(admin.ModelAdmin):
    # List view.
    list_display = ('timestamp', 'payment_link', 'level', 'message',
                    'related_payment_method', 'link_to_order_payment')
    list_filter = ('level',)
    search_fields = ('message', 'level', 'payment__id')
    readonly_fields = ('message', 'level', 'payment_link')
    fields = readonly_fields

    def link_to_order_payment(self, obj):
        payment = obj.payment.order_payment
        url = reverse('admin:{0}_{1}_change'.format(payment._meta.app_label,
                                                    payment._meta.model_name),
                      args=[payment.id])
        return format_html(
            u"<a href='{}'>Order Payment</a>",
            str(url)
        )

    link_to_order_payment.short_description = 'Related OrderPayment'

    def related_payment_method(self, obj):
        payment = obj.payment
        if not payment:
            return 'Payment not found!'
        if not payment.method_name:
            return 'Payment method not found!'
        return payment.method_name

    related_payment_method.short_description = 'Payment method'

    def payment_link(self, obj):
        # creates a link to the payment
        payment = obj.payment
        url = reverse('admin:{0}_{1}_change'.format(payment._meta.app_label,
                                                    payment._meta.model_name),
                      args=[payment.id])
        return format_html(
            u"<a href='{}'>{}: {}</a>",
            str(url),
            payment.polymorphic_ctype,
            payment.id
        )

    payment_link.short_description = "Related Payment"


admin.site.register(PaymentLogEntry, PaymentLogEntryAdmin)
