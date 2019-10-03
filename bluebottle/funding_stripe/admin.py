from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, PayoutAccountChildAdmin, \
    BankAccountChildAdmin
from bluebottle.funding.models import BankAccount, Payment, PaymentProvider
from bluebottle.funding_stripe.models import StripePayment, StripePaymentProvider, StripePayoutAccount, \
    StripeSourcePayment, ExternalAccount


@admin.register(StripePayment)
class StripePaymentAdmin(PaymentChildAdmin):
    base_model = StripePayment


@admin.register(StripeSourcePayment)
class StripeSourcePaymentAdmin(PaymentChildAdmin):
    base_model = Payment


@admin.register(StripePaymentProvider)
class PledgePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


class StripeBankAccountInline(admin.TabularInline):
    model = ExternalAccount
    readonly_fields = ['created', 'owner', 'verified', 'account_id', ]
    fields = readonly_fields
    extra = 0
    can_delete = False


@admin.register(StripePayoutAccount)
class StripePayoutAccountAdmin(PayoutAccountChildAdmin):
    model = StripePayoutAccount
    inlines = [StripeBankAccountInline]

    fields = PayoutAccountChildAdmin.fields + ('account_id', 'country')


@admin.register(ExternalAccount)
class StripeBankAccountAdmin(BankAccountChildAdmin):
    base_model = BankAccount
    model = ExternalAccount

    readonly_fields = BankAccountChildAdmin.readonly_fields + ('connect_link', )

    fields = ['owner', 'verified', 'funding_links', 'created', 'updated', 'account_id', 'connect_link']

    def connect_link(self, obj):
        url = reverse('admin:funding_payoutaccount_change', args=(obj.connect_account.id, ))
        return format_html('<a href="{}">{}</a>', url, obj.connect_account)
