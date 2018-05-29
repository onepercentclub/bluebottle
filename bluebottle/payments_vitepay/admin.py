from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import VitepayPayment


class VitepayPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = VitepayPayment
    raw_id_fields = ('order_payment', )


admin.site.register(VitepayPayment, VitepayPaymentAdmin)
