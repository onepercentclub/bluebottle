from django.contrib import admin
from django.core.urlresolvers import reverse

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment

from .models import Voucher, VoucherPayment


class VoucherPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = VoucherPayment

    readonly_fields = ('status', 'order_payment_link', 'voucher_link')
    fields = readonly_fields

    def order_payment_link(self, obj):
        object = obj.order_payment
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])
        return "<a href='{0}'>Order Payment: {1}</a>".format(str(url),
                                                             object.id)

    order_payment_link.allow_tags = True

    def voucher_link(self, obj):
        object = obj.voucher
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])
        return "<a href='{0}'>Voucher: {1}</a>".format(str(url), object.code)

    voucher_link.allow_tags = True


class VoucherAdmin(admin.ModelAdmin):
    list_filter = ('status',)
    search_fields = ('code', 'sender_email', 'receiver_email')
    list_display = ('created', 'code', 'amount', 'status', 'sender_email',
                    'receiver_email')
    raw_id_fields = ('sender', 'receiver')
    readonly_fields = ('view_order', 'payment_link')
    fields = readonly_fields + ('sender', 'receiver', 'status', 'amount',
                                'currency', 'code', 'sender_email',
                                'receiver_email', 'receiver_name',
                                'sender_name', 'message',)

    def view_order(self, obj):

        url = reverse('admin:%s_%s_change' % (obj.order._meta.app_label,
                                              obj.order._meta.model_name),
                      args=[obj.order.id])
        return "<a href='%s'>View Buy Order</a>" % (str(url))

    view_order.allow_tags = True

    def payment_link(self, obj):
        url = reverse('admin:%s_%s_change' % (obj.payment._meta.app_label,
                                              obj.payment._meta.model_name),
                      args=[obj.payment.id])
        return "<a href='%s'>Cash Voucher Payment</a>" % (str(url))

    payment_link.allow_tags = True


admin.site.register(Voucher, VoucherAdmin)
