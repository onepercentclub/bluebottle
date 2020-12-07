from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding.models import PaymentProvider, Payment
from bluebottle.funding_telesom.models import TelesomPayment, TelesomPaymentProvider, TelesomBankAccount


@admin.register(TelesomPayment)
class TelesomPaymentAdmin(PaymentChildAdmin):
    base_model = Payment
    fields = PaymentChildAdmin.fields + [
        'account_name', 'account_number', 'response', 'unique_id',
        'reference_id', 'transaction_id', 'transaction_amount', 'issuer_transaction_id',
        'amount', 'currency'
    ]


@admin.register(TelesomPaymentProvider)
class TelesomPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


@admin.register(TelesomBankAccount)
class TelesomBankAccountAdmin(BankAccountChildAdmin):
    model = TelesomBankAccount
    fields = ('account_name', 'mobile_number') + BankAccountChildAdmin.fields
    list_filter = ['reviewed']
    search_fields = ['account_name', 'mobile_number']
    list_display = ['created', 'account_name', 'mobile_number', 'reviewed']
