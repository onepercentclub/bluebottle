from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding.models import PaymentProvider, Payment
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaPaymentProvider, LipishaBankAccount


@admin.register(LipishaPayment)
class LipishaPaymentAdmin(PaymentChildAdmin):
    base_model = Payment
    readonly_fields = PaymentChildAdmin.readonly_fields
    fields = ['donation', 'mobile_number', 'transaction', 'unique_id', 'method'] + readonly_fields
    search_fields = ['mobile_number', 'transaction', 'unique_id']


@admin.register(LipishaPaymentProvider)
class LipishaPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


@admin.register(LipishaBankAccount)
class LipishaBankAccountAdmin(BankAccountChildAdmin):
    fields = (
        'mpesa_code',
        'payout_code',
        'account_number',
        'account_name',
        'bank_name',
        'bank_code',
        'branch_name',
        'branch_code',
        'address',
        'swift'
    ) + BankAccountChildAdmin.fields
    list_filter = ['reviewed']
    search_fields = ['mpesa_code', 'account_number', 'account_name']
    list_display = ['created', 'account_name', 'account_number', 'mpesa_code', 'reviewed']
