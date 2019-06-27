from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin
from bluebottle.funding_pledge.models import PledgePayment, PledgePaymentProvider


@admin.register(PledgePayment)
class PledgePaymentAdmin(PaymentChildAdmin):
    base_model = PledgePayment


@admin.register(PledgePaymentProvider)
class PledgePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PledgePaymentProvider
