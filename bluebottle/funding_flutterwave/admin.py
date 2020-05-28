from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding.models import Payment, PaymentProvider
from bluebottle.funding_flutterwave.models import FlutterwavePayment, FlutterwavePaymentProvider, \
    FlutterwaveBankAccount


@admin.register(FlutterwavePayment)
class FlutterwavePaymentAdmin(PaymentChildAdmin):
    base_model = Payment

    search_fields = ['tx_ref', ]
    list_display = ['__unicode__', 'created', 'status', 'tx_ref']


@admin.register(FlutterwavePaymentProvider)
class FlutterwavePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


@admin.register(FlutterwaveBankAccount)
class FlutterwaveBankAccountAdmin(BankAccountChildAdmin):
    model = FlutterwaveBankAccount

    fields = BankAccountChildAdmin.fields + (
        'account_holder_name', 'bank_country_code',
        'bank_code', 'account_number', 'account')
    list_filter = ['bank_code', 'reviewed']
    search_fields = ['account_holder_name', 'account_number']
    list_display = ['created', 'account_holder_name', 'account_number', 'bank_code', 'reviewed']
