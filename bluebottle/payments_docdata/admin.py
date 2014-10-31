from bluebottle.payments_logger.admin import PaymentLogEntryInline
from django.core.urlresolvers import reverse
from bluebottle.payments.models import Payment
from bluebottle.payments_docdata.models import DocdataPayment
from polymorphic.admin import PolymorphicChildModelAdmin


class DocdataPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = DocdataPayment

    inlines = (PaymentLogEntryInline, )

    readonly_fields = ('order_payment_link', 'payment_cluster_link', 'payment_cluster_key',
                       'ideal_issuer_id', 'default_pm', 'total_gross_amount', 'currency',
                       'total_registered', 'total_shopper_pending',
                       'total_acquirer_pending', 'total_acquirer_approved',
                       'total_captured', 'total_refunded', 'total_charged_back')

    fields = ('status', ) + readonly_fields

    def order_payment_link(self, obj):
        object = obj.order_payment
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>Order Payment: {1}</a>".format(str(url), object.id)

    order_payment_link.allow_tags = True


    def payment_cluster_link(selfself, obj):
        url = 'https://backoffice.docdatapayments.com/ps/com.tripledeal.paymentservice.backoffice.MerchantReportPayoutTransaction'
        return '{1} <a href="{0}" target="docdata">[Docdata Backoffice]</a>'.format(url, obj.payment_cluster_id)

    payment_cluster_link.allow_tags = True