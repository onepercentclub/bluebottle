from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import BeyonicPayment


class BeyonicPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = BeyonicPayment
    search_fields = ['mobile', ]
    raw_id_fields = ('order_payment', )
    readonly_fields = ('amount', 'currency', 'transaction_reference',
                       'metadata', 'mobile', 'description',
                       'response', 'update_response')
