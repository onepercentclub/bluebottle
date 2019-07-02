from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin
from bluebottle.funding_stripe.models import StripePayment, StripePaymentProvider


@admin.register(StripePayment)
class StripePaymentAdmin(PaymentChildAdmin):
    base_model = StripePayment


@admin.register(StripePaymentProvider)
class PledgePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = StripePaymentProvider
