from django.contrib import admin, messages
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
    readonly_fields = ['bank_account_link', 'verified', 'account_id', ]
    fields = readonly_fields
    extra = 0
    can_delete = False

    def bank_account_link(self, obj):
        url = reverse('admin:funding_stripe_externalaccount_change', args=(obj.id, ))
        return format_html('<a href="{}">{}</a>', url, obj)


@admin.register(StripePayoutAccount)
class StripePayoutAccountAdmin(PayoutAccountChildAdmin):
    model = StripePayoutAccount
    inlines = [StripeBankAccountInline]
    readonly_fields = PayoutAccountChildAdmin.readonly_fields + ['reviewed']
    search_fields = ['account_id']
    fields = ('created', 'owner', 'status', 'account_id', 'country', 'reviewed')

    def save_model(self, request, obj, form, change):
        if 'ba_' in obj.account_id:
            obj.account_id = ''
            self.message_user(
                request,
                'This Account id should start with acct_ The ba_ number is for the StripeBankAccount',
                messages.ERROR
            )
        if obj.account_id \
                and StripePayoutAccount.objects.exclude(id=obj.id).filter(account_id=obj.account_id).count():
            obj.account_id = ''
            self.message_user(
                request,
                'There is already a StripePayoutAccount with this account_id.',
                messages.ERROR
            )
        return super(StripePayoutAccountAdmin, self).save_model(request, obj, form, change)


@admin.register(ExternalAccount)
class StripeBankAccountAdmin(BankAccountChildAdmin):
    base_model = BankAccount
    model = ExternalAccount
    fields = ('connect_account', 'account_id') + BankAccountChildAdmin.readonly_fields

    list_filter = ['reviewed']
    search_fields = ['account_id']
    list_display = ['created', 'account_id', 'reviewed']

    def save_model(self, request, obj, form, change):
        if 'acct_' in obj.account_id:
            obj.account_id = ''
            self.message_user(
                request,
                'This Account id should start with ba_ The acct_. number is for the StripePayoutAccount',
                messages.ERROR
            )
        if obj.account_id \
                and ExternalAccount.objects.exclude(id=obj.id).filter(account_id=obj.account_id).count():
            obj.account_id = ''
            self.message_user(
                request,
                'There is already a StripeBankAccount with this account_id.',
                messages.ERROR
            )
        return super(StripeBankAccountAdmin, self).save_model(request, obj, form, change)
