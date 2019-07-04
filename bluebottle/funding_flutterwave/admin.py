from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwavePaymentProvider


@admin.register(FlutterwavePayment)
class FlutterwavePaymentAdmin(PaymentChildAdmin):
    base_model = FlutterwavePayment


@admin.register(FlutterwavePaymentProvider)
class FlutterwavePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = FlutterwavePaymentProvider
