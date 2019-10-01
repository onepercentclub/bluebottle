from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding.models import PaymentProvider
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayPaymentProvider, VitepayBankAccount


@admin.register(VitepayPayment)
class VitepayPaymentAdmin(PaymentChildAdmin):
    base_model = VitepayPayment


@admin.register(VitepayPaymentProvider)
class VitepayPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


@admin.register(VitepayBankAccount)
class VitepayBankAccountAdmin(BankAccountChildAdmin):
    model = VitepayBankAccount
    fields = BankAccountChildAdmin.fields + ('account_name', )
