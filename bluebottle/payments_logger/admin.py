from django.contrib import admin
from django.core.urlresolvers import reverse
from bluebottle.payments_logger.models import PaymentLogEntry


class PaymentLogEntryAdmin(admin.ModelAdmin):
    # List view.
    list_display = ('payment', 'payment_link', 'timestamp', 'level', 'message', 'related_payment_method', 'link_to_order_payment')
    list_filter = ('level',)
    search_fields = ('message', 'level', 'payment')

    def link_to_order_payment(self, obj):
        payment = obj.payment.order_payment
        url = reverse('admin:{0}_{1}_change'.format(payment._meta.app_label, payment._meta.module_name), args=[payment.id])
        return "<a href='{0}'>Order Payment</a>".format(str(url))

    link_to_order_payment.short_description = 'Link to OrderPayment'
    link_to_order_payment.allow_tags = True

    def related_payment_method(self, obj):
        return obj.payment.order_payment.payment_method

    related_payment_method.short_description = 'Payment Provider & Method'

    def payment_link(self, obj):
        # creates a link to the payment
        payment = obj.payment
        url = reverse('admin:{0}_{1}_change'.format(payment._meta.app_label, payment._meta.module_name), args=[payment.id])
        return "<a href='{0}'>{1}: {2}</a>".format(str(url), payment.polymorphic_ctype, payment._meta.module_name)

    payment_link.allow_tags = True
    # payment.allow_tags = True

    # # Don't allow the detail view to be accessed.
    # def has_change_permission(self, request, obj=None):
    #     if not obj:
    #         return True
    #     return False

admin.site.register(PaymentLogEntry, PaymentLogEntryAdmin)
