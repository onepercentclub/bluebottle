from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from .models import FlutterwavePayment, FlutterwaveMpesaPayment


class FlutterwavePaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = FlutterwavePayment
    raw_id_fields = ('order_payment', )
    readonly_fields = ('transaction_reference', 'response', 'update_response')


class FlutterwaveMpesaPaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = FlutterwaveMpesaPayment
    raw_id_fields = ('order_payment', )
    readonly_fields = ('business_number', 'account_number',
                       'kyc_info', 'msisdn', 'invoice_number',
                       'third_party_transaction_id',
                       'remote_id', 'transaction_amount',
                       'transaction_time', 'transaction_reference',
                       'response', 'update_response')
