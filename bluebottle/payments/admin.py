from django.conf.urls import url
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db import connection
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.utils.html import format_html

from polymorphic.admin import (PolymorphicParentModelAdmin,
                               PolymorphicChildModelAdmin)

from bluebottle.clients import properties
from bluebottle.payments.exception import PaymentException
from bluebottle.payments.models import Payment, OrderPayment
from bluebottle.payments.services import PaymentService
from bluebottle.payments.tasks import check_payment_statuses
from bluebottle.payments_beyonic.admin import BeyonicPaymentAdmin
from bluebottle.payments_external.admin import ExternalPaymentAdmin
from bluebottle.payments_flutterwave.admin import FlutterwavePaymentAdmin, FlutterwaveMpesaPaymentAdmin
from bluebottle.payments_interswitch.admin import InterswitchPaymentAdmin
from bluebottle.payments_docdata.admin import (
    DocdataPaymentAdmin,
    DocdataDirectdebitPaymentAdmin)
from bluebottle.payments_lipisha.admin import LipishaPaymentAdmin
from bluebottle.payments_logger.admin import PaymentLogEntryInline
from bluebottle.payments_telesom.admin import TelesomPaymentAdmin
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
        process_urls = [
            url(r'^check/(?P<pk>\d+)/$', self.check_status, name="payments_orderpayment_check"),
            url(r'^refund/(?P<pk>\d+)/$', self.refund, name="payments_orderpayment_refund"),
        ]
        return process_urls + urls

    def check_status(self, request, pk=None):
        order_payment = OrderPayment.objects.get(pk=pk)
        service = PaymentService(order_payment)
        try:
            service.check_payment_status()
        except PaymentException as e:
            self.message_user(
                request,
                'Error checking status {}'.format(e),
                level='WARNING'
            )
        order_payment_url = reverse('admin:payments_orderpayment_change', args=(order_payment.id,))
        response = HttpResponseRedirect(order_payment_url)
        return response

    def batch_check_status(self, request, queryset):
        if getattr(properties, 'CELERY_RESULT_BACKEND', None):
            check_payment_statuses.delay(queryset, connection.tenant)
            self.message_user(
                request,
                'Batch process to check statuses is scheduled, please check the order '
                'payments after a couple of minutes to see the result.',
                level='INFO'
            )
        else:
            check_payment_statuses(queryset, connection.tenant)

    def refund(self, request, pk=None):
        if not request.user.has_perm('payments.refund_orderpayment') or not properties.ENABLE_REFUNDS:
            return HttpResponseForbidden('Missing permission: payments.refund_orderpayment')

        order_payment = OrderPayment.objects.get(pk=pk)

        service = PaymentService(order_payment)

        service.refund_payment()

        self.message_user(
            request,
            'Refund is requested. It may take a while for this to be visble here'
        )

        order_payment_url = reverse('admin:payments_orderpayment_change', args=(order_payment.id,))
        response = HttpResponseRedirect(order_payment_url)

        return response

    batch_check_status.short_description = 'Check status at PSP'

    def order_link(self, obj):
        object = obj.order
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])
        return format_html(
            u"<a href='{}'>Order: {}</a>",
            str(url), object.id
        )

    def payment_link(self, obj):
        object = obj.payment
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])
        return format_html(
            u"<a href='{}'>{}: {}</a>",
            str(url),
            object.polymorphic_ctype,
            object.id
        )


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
        return format_html("<a href='{0}'>OrderPayment {1}</a>", str(url), obj.id)

    def has_add_permission(self, request):
        return False


class PaymentAdmin(PolymorphicParentModelAdmin):
    base_model = Payment
    list_display = ('created', 'status', 'order_payment_amount', 'polymorphic_ctype')
    list_filter = ('status', )

    inlines = (PaymentLogEntryInline,)
    ordering = ('-created',)

    def get_child_models(self):
        return tuple(
            (admin.model, admin) for admin in (
                DocdataPaymentAdmin, DocdataDirectdebitPaymentAdmin,
                VoucherPaymentAdmin, InterswitchPaymentAdmin,
                FlutterwavePaymentAdmin, FlutterwaveMpesaPaymentAdmin,
                LipishaPaymentAdmin, TelesomPaymentAdmin, VitepayPaymentAdmin,
                BeyonicPaymentAdmin, ExternalPaymentAdmin
            )
        )

    def order_payment_amount(self, instance):
        return instance.order_payment.amount


admin.site.register(Payment, PaymentAdmin)


class BasePaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
