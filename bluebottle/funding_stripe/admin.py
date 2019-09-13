from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, PayoutAccountChildAdmin
from bluebottle.funding_stripe.models import StripePayment, StripePaymentProvider, StripePayoutAccount, \
    StripeSourcePayment


@admin.register(StripePayment)
class StripePaymentAdmin(PaymentChildAdmin):
    base_model = StripePayment


@admin.register(StripeSourcePayment)
class StripeSourcePaymentAdmin(PaymentChildAdmin):
    base_model = StripeSourcePayment


@admin.register(StripePaymentProvider)
class PledgePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = StripePaymentProvider


@admin.register(StripePayoutAccount)
class StripePayoutAccountAdmin(PayoutAccountChildAdmin):
    model = StripePayoutAccount

    fields = PayoutAccountChildAdmin.fields + ('account_id', 'country')
