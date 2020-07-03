from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding.models import PaymentProvider, Payment
from bluebottle.funding_vitepay.models import VitepayPayment, VitepayPaymentProvider, VitepayBankAccount


@admin.register(VitepayPayment)
class VitepayPaymentAdmin(PaymentChildAdmin):
    base_model = Payment


@admin.register(VitepayPaymentProvider)
class VitepayPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


@admin.register(VitepayBankAccount)
class VitepayBankAccountAdmin(BankAccountChildAdmin):
    model = VitepayBankAccount
    fields = BankAccountChildAdmin.fields + ('account_name', 'mobile_number')
    list_filter = ['reviewed']
    search_fields = ['account_name', 'mobile_number']
    list_display = ['created', 'account_name', 'mobile_number', 'reviewed']
