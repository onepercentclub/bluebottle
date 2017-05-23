from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import LipishaPayment


class LipishaPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = LipishaPayment
    search_fields = ['transaction_mobile', 'transaction_reference']
    raw_id_fields = ('order_payment', )
