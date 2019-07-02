from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayPaymentProvider


@admin.register(VitepayPayment)
class VitepayPaymentAdmin(PaymentChildAdmin):
    base_model = VitepayPayment


@admin.register(VitepayPaymentProvider)
class PledgePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = VitepayPaymentProvider
