from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payments.models import Payment
from bluebottle.payments_stripe.models import StripePayment


class StripePaymentAdmin(PolymorphicChildModelAdmin):
    base_model = Payment
    model = StripePayment
    search_fields = ['token', 'transaction_reference']
    raw_id_fields = ('order_payment', )
    # readonly_fields = ('amount', 'currency',
    #                    'description',
    #                    'transaction_reference',
    #                    'response', 'update_response')


admin.site.register(StripePayment, StripePaymentAdmin)
