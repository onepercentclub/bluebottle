from django.contrib import admin
from django.contrib.admin.templatetags.admin_static import static
from django.core.urlresolvers import reverse

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
                                                    payment._meta.module_name),
                      args=[payment.id])
        return "<a href='{0}'>Order Payment</a>".format(str(url))

    link_to_order_payment.short_description = 'Related OrderPayment'
    link_to_order_payment.allow_tags = True

    def related_payment_method(self, obj):
        order_payment = obj.payment.order_payment
        if not order_payment or not order_payment.payment:
            return '?'
        icon = static(order_payment.payment.method_icon)
        return '<img src="{0}" height="16px" title="{1}" />'.format(
            icon, order_payment.payment.method_name)

    related_payment_method.short_description = 'Payment method'
    related_payment_method.allow_tags = True

    def payment_link(self, obj):
        # creates a link to the payment
        payment = obj.payment
        url = reverse('admin:{0}_{1}_change'.format(payment._meta.app_label,
                                                    payment._meta.module_name),
                      args=[payment.id])
        return "<a href='{0}'>{1}: {2}</a>".format(str(url),
                                                   payment.polymorphic_ctype,
                                                   payment.id)

    payment_link.short_description = "Related Payment"
    payment_link.allow_tags = True


admin.site.register(PaymentLogEntry, PaymentLogEntryAdmin)
