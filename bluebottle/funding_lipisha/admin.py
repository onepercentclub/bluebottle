from django.contrib import admin

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding_lipisha.models import LipishaPayment, LipishaPaymentProvider, LipishaBankAccount


@admin.register(LipishaPayment)
class LipishaPaymentAdmin(PaymentChildAdmin):
    base_model = LipishaPayment


@admin.register(LipishaPaymentProvider)
class LipishaPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = LipishaPaymentProvider


@admin.register(LipishaBankAccount)
class LipishaBankAccountAdmin(BankAccountChildAdmin):
    model = LipishaBankAccount
    fields = BankAccountChildAdmin.fields + ('account_number',)
