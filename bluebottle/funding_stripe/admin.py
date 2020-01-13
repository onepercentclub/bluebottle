from django.conf.urls import url
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.clients import properties
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
    readonly_fields = PayoutAccountChildAdmin.readonly_fields + ['reviewed', 'account_details', 'stripe_link']
    search_fields = ['account_id']
    fields = ['created', 'owner', 'status', 'account_id', 'country', 'account_details']
    list_display = ['id', 'account_id', 'status']

    def get_fields(self, request, obj=None):
        fields = super(StripePayoutAccountAdmin, self).get_fields(request, obj)
        if request.user.is_superuser:
            fields = fields + ['stripe_link']
        return fields

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

    def get_urls(self):
        urls = super(StripePayoutAccountAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<account_id>.+)/check_status/$',
                self.admin_site.admin_view(self.check_status),
                name='funding-stripe-account-check',
            ),
        ]
        return custom_urls + urls

    def check_status(self, request, account_id):
        account = StripePayoutAccount.objects.get(id=account_id)
        account.check_status()
        payout_url = reverse('admin:funding_payoutaccount_change', args=(account_id,))
        return HttpResponseRedirect(payout_url)

    check_status.short_description = _('Check status at Stripe')

    def account_details(self, obj):
        individual = obj.account.get('individual')
        if individual:
            if obj.status == 'verified':
                template = loader.get_template(
                    'admin/funding_stripe/stripepayoutaccount/detail_fields.html'
                )
                return template.render({'info': individual})
            elif obj.status == 'pending':
                return _('Pending verification')
            else:
                req = individual['requirements']
                fields = req['currently_due'] + req['eventually_due'] + req['past_due']
                template = loader.get_template(
                    'admin/funding_stripe/stripepayoutaccount/missing_fields.html'
                )
                return template.render({'fields': fields})

        return _('All info missing')
    account_details.short_description = _('Details')

    def stripe_link(self, obj):
        if properties.LIVE_PAYMENTS_ENABLED:
            url = 'https://dashboard.stripe.com/test/connect/accounts/{}'.format(obj.account_id)
        else:
            url = 'https://dashboard.stripe.com/test/connect/accounts/{}'.format(obj.account_id)
        return format_html(
            '<a href="{}" target="_blank">{}</a><br/>'
            '<small>{}</small>',
            url, obj.account_id,
            _('This is only visible for superadmin accounts.')
        )
    stripe_link.short_description = _('Stripe link')


@admin.register(ExternalAccount)
class StripeBankAccountAdmin(BankAccountChildAdmin):
    base_model = BankAccount
    model = ExternalAccount
    readonly_fields = BankAccountChildAdmin.readonly_fields + ('account_details',)
    fields = ('connect_account', 'account_id', 'account_details') + BankAccountChildAdmin.readonly_fields

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

    def account_details(self, obj):
        template = loader.get_template(
            'admin/funding_stripe/stripebankaccount/detail_fields.html'
        )
        return template.render({'info': obj.account})
    account_details.short_description = _('Details')
