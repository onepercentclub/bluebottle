from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import ExternalPayment


class ExternalPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = ExternalPayment
    raw_id_fields = ('order_payment', )
