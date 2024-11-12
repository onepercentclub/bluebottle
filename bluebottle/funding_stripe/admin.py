from django.conf.urls import url
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.forms import ChoiceField
from django.template import loader
from django.urls import reverse
from django.utils.html import format_html, mark_safe
from django.utils.translation import gettext_lazy as _
from stripe.error import StripeError

from bluebottle.funding_stripe.utils import get_stripe
from bluebottle.fsm.forms import StateMachineModelForm

from bluebottle.geo.models import Country

from bluebottle.clients import properties
from bluebottle.funding.admin import PaymentChildAdmin, PaymentProviderChildAdmin, PayoutAccountChildAdmin, \
    BankAccountChildAdmin
from bluebottle.funding.models import BankAccount, Payment, PaymentProvider
from bluebottle.funding_stripe.models import StripePayment, StripePaymentProvider, StripePayoutAccount, \
    StripeSourcePayment, ExternalAccount, PaymentIntent


@admin.register(StripePayment)
class StripePaymentAdmin(PaymentChildAdmin):
    raw_id_fields = PaymentChildAdmin.raw_id_fields + ['payment_intent']
    base_model = StripePayment
    list_display = ['created', 'donation', 'status']
    search_fields = ['paymentintent__intent_id']
    readonly_fields = PaymentChildAdmin.readonly_fields
    fields = PaymentChildAdmin.fields + ['payment_intent']


@admin.register(PaymentIntent)
class StripePaymentIntentAdmin(admin.ModelAdmin):
    model = PaymentIntent
    raw_id_fields = ['donation']
    list_display = ['intent_id', 'created', 'donation']


@admin.register(StripeSourcePayment)
class StripeSourcePaymentAdmin(PaymentChildAdmin):
    base_model = Payment
    readonly_fields = PaymentChildAdmin.readonly_fields
    fields = PaymentChildAdmin.fields + ['source_token', 'charge_token']


@admin.register(StripePaymentProvider)
class PledgePaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = PaymentProvider


class StripeBankAccountInline(admin.TabularInline):
    model = ExternalAccount
    readonly_fields = ['bank_account_link', 'status', 'account_id', ]
    fields = readonly_fields
    extra = 0
    can_delete = False

    def bank_account_link(self, obj):
        url = reverse('admin:funding_stripe_externalaccount_change', args=(obj.id, ))
        return format_html('<a href="{}">{}</a>', url, obj)


class StripePayoutAccountForm(StateMachineModelForm):
    country = ChoiceField(label=_('Country'), required=True, choices=())

    def __init__(self, *args, **kwargs):

        stripe = get_stripe()
        countries = Country.objects.filter(
            alpha2_code__in=(
                spec.id for spec in stripe.CountrySpec.list(limit=200)
            )
        )
        self.base_fields['country'].choices = [
            (country.code, country.name) for country in countries
        ]

        self.base_fields['business_type'].required = True
        super().__init__(*args, **kwargs)


@admin.register(StripePayoutAccount)
class StripePayoutAccountAdmin(PayoutAccountChildAdmin):
    form = StripePayoutAccountForm
    model = StripePayoutAccount
    inlines = [StripeBankAccountInline]
    readonly_fields = PayoutAccountChildAdmin.readonly_fields + [
        "verified",
        "payments_enabled",
        "payouts_enabled",
        "funding",
        "stripe_link",
        'requirements_list',
        'verification_link',
    ]
    search_fields = ["account_id"]
    fields = PayoutAccountChildAdmin.fields + [
        "business_type",
        "country", 'payments_enabled', 'payouts_enabled', 'requirements_list',
        'verification_link',
        'partner_organization'
    ]

    list_display = ["id", "account_id", "owner", "status"]

    def get_fields(self, request, obj=None):

        fields = super(StripePayoutAccountAdmin, self).get_fields(request, obj)

        if obj:
            if request.user.is_superuser:
                fields = fields + ['stripe_link']
            fields += ['account_id', 'funding', ]

        return fields

    def save_model(self, request, obj, form, change):
        if obj.account_id and 'ba_' in obj.account_id:
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
        individual = obj.account.get('individual', None)
        business = obj.account.get('business_profile', None)
        if individual:
            if obj.status == 'verified':
                template = loader.get_template(
                    'admin/funding_stripe/stripepayoutaccount/detail_fields.html'
                )
                return template.render({'info': individual})
            elif obj.status == 'pending':
                return _('Pending verification')
            else:
                template = loader.get_template(
                    'admin/funding_stripe/stripepayoutaccount/missing_fields.html'
                )
                return template.render({'fields': obj.missing_fields})
        elif business:
            if obj.status == 'verified':
                template = loader.get_template(
                    'admin/funding_stripe/stripepayoutaccount/business_fields.html'
                )
                return template.render({'info': business})
            elif obj.status == 'pending':
                return _('Pending verification')
            else:
                template = loader.get_template(
                    'admin/funding_stripe/stripepayoutaccount/missing_fields.html'
                )
                return template.render({'fields': obj.missing_fields})

        return _('All info missing')
    account_details.short_description = _('Details')

    def stripe_link(self, obj):
        if properties.LIVE_PAYMENTS_ENABLED:
            url = 'https://dashboard.stripe.com/connect/accounts/{}'.format(obj.account_id)
        else:
            url = 'https://dashboard.stripe.com/test/connect/accounts/{}'.format(obj.account_id)
        return format_html(
            '<a href="{}" target="_blank">{}</a><br/>'
            '<small>{}</small>',
            url, obj.account_id,
            _('This is only visible for superadmin accounts.')
        )
    stripe_link.short_description = _('Stripe link')

    def requirements_list(self, obj):
        return format_html('<ul>{}</ul>', mark_safe(''.join(
            format_html('<li>{}</li>', requirement.split('.')[-1])
            for requirement in obj.requirements
        )))
    requirements_list.short_description = _('Requirements')


@admin.register(ExternalAccount)
class StripeBankAccountAdmin(BankAccountChildAdmin):
    base_model = BankAccount
    model = ExternalAccount
    readonly_fields = ('status', 'account_details') + BankAccountChildAdmin.readonly_fields
    fields = ('connect_account', 'account_id', 'logo', 'description') + readonly_fields

    list_filter = ['reviewed']
    search_fields = ['account_id']
    list_display = ['created', 'account_id', 'status']

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Basic'), {'fields': self.get_fields(request, obj)}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': ['force_status']}),
            )
        return fieldsets

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
        try:
            template = loader.get_template(
                'admin/funding_stripe/stripebankaccount/detail_fields.html'
            )
            return template.render({'info': obj.account})
        except StripeError as e:
            return "Error retrieving details: {}".format(e)
    account_details.short_description = _('Details')
