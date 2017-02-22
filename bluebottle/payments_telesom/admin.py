from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import TelesomPayment


class TelesomPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = TelesomPayment
    search_fields = ['mobile', 'transaction_reference']
    raw_id_fields = ('order_payment', )
    readonly_fields = ('amount', 'currency', 'mobile',
                       'description',
                       'transaction_reference',
                       'response', 'update_response')
