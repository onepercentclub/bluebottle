from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, PayoutAccountChildAdmin
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayPaymentProvider, VitepayPayoutAccount


@admin.register(VitepayPayment)
class VitepayPaymentAdmin(PaymentChildAdmin):
    base_model = VitepayPayment


@admin.register(VitepayPaymentProvider)
class VitepayPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = VitepayPaymentProvider


@admin.register(VitepayPayoutAccount)
class VitepayPayoutAccountAdmin(PayoutAccountChildAdmin):
    model = VitepayPayoutAccount
    fields = PayoutAccountChildAdmin.fields + ('account_name',)
