from django.contrib import admin


from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import FlutterwavePayment


class FlutterwavePaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = FlutterwavePayment
    raw_id_fields = ('order_payment', )
    readonly_fields = ('transaction_reference', 'response', 'update_response')


admin.site.register(FlutterwavePayment, FlutterwavePaymentAdmin)
