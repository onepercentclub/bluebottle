from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, BankAccountChildAdmin
from bluebottle.funding.models import PaymentProvider, Payment
from bluebottle.funding_pledge.models import PledgePayment, PledgePaymentProvider, PledgeBankAccount


@admin.register(PledgePayment)
class PledgePaymentAdmin(PaymentChildAdmin):
    base_model = Payment


@admin.register(PledgePaymentProvider)
class PledgePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider

    readonly_fields = ('settings',)
    fields = readonly_fields

    def settings(self, obj):
        return _('No settings are required for this payment provider')


@admin.register(PledgeBankAccount)
class PledgeBankAccountAdmin(BankAccountChildAdmin):
    model = PledgeBankAccount
    fields = BankAccountChildAdmin.fields + (
        'account_holder_name',
        'account_holder_address',
        'account_holder_postal_code',
        'account_holder_city',
        'account_holder_country',
        'account_number',
        'account_details',
        'account_bank_country'
    )
