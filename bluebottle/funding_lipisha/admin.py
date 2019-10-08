from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding.models import PaymentProvider, Payment
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaPaymentProvider, LipishaBankAccount


@admin.register(LipishaPayment)
class LipishaPaymentAdmin(PaymentChildAdmin):
    base_model = Payment


@admin.register(LipishaPaymentProvider)
class LipishaPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


@admin.register(LipishaBankAccount)
class LipishaBankAccountAdmin(BankAccountChildAdmin):
    model = LipishaBankAccount
    fields = BankAccountChildAdmin.fields + (
        'account_number',
        'account_name',
        'bank_name',
        'bank_code',
        'branch_name',
        'branch_code',
        'address',
        'swift'
    )
