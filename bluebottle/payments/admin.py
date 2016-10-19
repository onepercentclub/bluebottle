from django.conf.urls import patterns, url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect

from polymorphic.admin import (PolymorphicParentModelAdmin,
                               PolymorphicChildModelAdmin)

from bluebottle.payments.models import Payment, OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.payments_interswitch.admin import InterswitchPaymentAdmin
from bluebottle.payments_docdata.admin import (
    DocdataPaymentAdmin,
    DocdataDirectdebitPaymentAdmin)
from bluebottle.payments_logger.admin import PaymentLogEntryInline
from bluebottle.payments_vitepay.admin import VitepayPaymentAdmin
from bluebottle.payments_voucher.admin import VoucherPaymentAdmin


class OrderPaymentAdmin(admin.ModelAdmin):
    model = OrderPayment
    raw_id_fields = ('user',)
    readonly_fields = ('order_link', 'payment_link', 'authorization_action',
                       'amount', 'integration_data', 'payment_method',
                       'transaction_fee', 'status', 'created', 'closed')
    fields = ('user',) + readonly_fields
    list_display = ('created', 'user', 'status', 'amount',
                    'payment_method', 'transaction_fee')

    list_filter = ('status', 'payment_method')
    ordering = ('-created',)

    actions = ['batch_check_status']

    def get_urls(self):
        urls = super(OrderPaymentAdmin, self).get_urls()
        process_urls = patterns(
            '',
            url(r'^check/(?P<pk>\d+)/$', self.check_status, name="payments_orderpayment_check")
        )
        return process_urls + urls

    def check_status(self, request, pk=None):
        order_payment = OrderPayment.objects.get(pk=pk)
        service = PaymentService(order_payment)
        service.check_payment_status()
        order_payment_url = reverse('admin:payments_orderpayment_change', args=(order_payment.id,))
        response = HttpResponseRedirect(order_payment_url)
        return response

    def batch_check_status(self, request, queryset):
        for order_payment in queryset:
            service = PaymentService(order_payment)
            service.check_payment_status()

    batch_check_status.short_description = 'Check status at PSP'

    def order_link(self, obj):
        object = obj.order
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])
        return "<a href='{0}'>Order: {1}</a>".format(str(url), object.id)

    order_link.allow_tags = True

    def payment_link(self, obj):
        object = obj.payment
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])
        return "<a href='{0}'>{1}: {2}</a>".format(str(url),
                                                   object.polymorphic_ctype,
                                                   object.id)

    payment_link.allow_tags = True


admin.site.register(OrderPayment, OrderPaymentAdmin)


class OrderPaymentInline(admin.TabularInline):
    model = OrderPayment
    extra = 0
    can_delete = False
    max_num = 0
    readonly_fields = ('order_payment_link', 'amount', 'user',
                       'payment_method', 'status')
    fields = readonly_fields

    def order_payment_link(self, obj):
        object = obj
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])
        return "<a href='{0}'>OrderPayment {1}</a>".format(str(url), obj.id)

    order_payment_link.allow_tags = True

    def has_add_permission(self, request):
        return False


class PaymentAdmin(PolymorphicParentModelAdmin):
    base_model = Payment
    list_display = ('created', 'order_payment_amount', 'polymorphic_ctype')

    inlines = (PaymentLogEntryInline,)
    ordering = ('-created',)

    def get_child_models(self):
        return tuple(
            (admin.model, admin) for admin in (
                DocdataPaymentAdmin, DocdataDirectdebitPaymentAdmin,
                VoucherPaymentAdmin, InterswitchPaymentAdmin,
                VitepayPaymentAdmin
            )
        )

    def order_payment_amount(self, instance):
        return instance.order_payment.amount


admin.site.register(Payment, PaymentAdmin)


class BasePaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
