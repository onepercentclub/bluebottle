from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import InterswitchPayment


class InterswitchPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = InterswitchPayment
    raw_id_fields = ('order_payment', )
