from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import TelesomPayment


class TelesomPaymentPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = TelesomPayment
    raw_id_fields = ('order_payment', )
    readonly_fields = ('amount', 'currency', 'response', 'update_response')
