from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin
from bluebottle.funding_stripe.models import StripePayment


@admin.register(StripePayment)
class StripePaymentAdmin(PaymentChildAdmin):
    base_model = StripePayment
