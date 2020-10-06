from __future__ import division
from past.utils import old_div
from builtins import object
import logging

from babel.numbers import get_currency_symbol
from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin import TabularInline, SimpleListFilter
from django.db import models
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from polymorphic.admin import PolymorphicChildModelAdmin
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic.admin.parentadmin import PolymorphicParentModelAdmin

from bluebottle.activities.admin import ActivityChildAdmin, ContributionChildAdmin
from bluebottle.bluebottle_dashboard.decorators import confirmation_form
from bluebottle.fsm.admin import StateMachineAdmin, StateMachineAdminMixin, StateMachineFilter
from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.filters import DonationAdminStatusFilter, DonationAdminCurrencyFilter, DonationAdminPledgeFilter
from bluebottle.funding.forms import RefundConfirmationForm
from bluebottle.funding.models import (
    Funding, Donation, Payment, PaymentProvider,
    BudgetLine, PayoutAccount, LegacyPayment, BankAccount, PaymentCurrency, PlainPayoutAccount, Payout, Reward,
    FundingPlatformSettings)
from bluebottle.funding.states import DonationStateMachine
from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider, FlutterwaveBankAccount, \
    FlutterwavePayment
from bluebottle.funding_lipisha.models import LipishaPaymentProvider, LipishaBankAccount, LipishaPayment
from bluebottle.funding_pledge.models import PledgePayment, PledgePaymentProvider, PledgeBankAccount
from bluebottle.funding_stripe.models import StripePaymentProvider, StripePayoutAccount, \
    StripeSourcePayment, ExternalAccount, StripePayment
from bluebottle.funding_telesom.models import TelesomPaymentProvider, TelesomPayment
from bluebottle.funding_vitepay.models import VitepayPaymentProvider, VitepayBankAccount, VitepayPayment
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import TotalAmountAdminChangeList, export_as_csv_action, BasePlatformSettingsAdmin
from bluebottle.wallposts.admin import DonationWallpostInline

logger = logging.getLogger(__name__)


class PaymentLinkMixin(object):

    def payment_link(self, obj):
        payment_url = reverse('admin:{}_{}_change'.format(
            obj.payment._meta.app_label, obj.payment._meta.model_name,
        ), args=(obj.payment.id,))
        return format_html('<a href="{}">{}</a>', payment_url, obj.payment)

    payment_link.short_description = _('Payment')


class BudgetLineInline(admin.TabularInline):
    model = BudgetLine
    readonly_fields = ['created']

    extra = 0


class RewardInline(admin.TabularInline):
    model = Reward
    readonly_fields = ('link', 'amount', 'description',)
    extra = 0

    def link(self, obj):
        url = reverse('admin:funding_reward_change', args=(obj.id,))
        return format_html(u'<a href="{}">{}</a>', url, obj.title)


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    model = Reward
    raw_id_fields = ['activity']


class CurrencyFilter(SimpleListFilter):

    title = _('Currency')
    parameter_name = 'currency'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(target_currency=self.value())
        return queryset

    def lookups(self, request, model_admin):
        return [
            (cur, get_currency_symbol(cur)) for cur in
            Funding.objects.values_list('target_currency', flat=True).distinct()
        ]


class PayoutInline(StateMachineAdminMixin, admin.TabularInline):

    model = Payout
    readonly_fields = [
        'payout_link', 'total_amount', 'status', 'provider', 'currency',
        'date_approved', 'date_started', 'date_completed'
    ]
    fields = readonly_fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request):
        return False

    def payout_link(self, obj):
        url = reverse('admin:funding_payout_change', args=(obj.id, ))
        return format_html(u'<a href="{}">{}</a>', url, obj)


class FundingAdminForm(StateMachineModelForm):

    class Meta(object):
        model = Funding
        exclude = ('contribution_date', )
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


@admin.register(Funding)
class FundingAdmin(ActivityChildAdmin):
    inlines = (BudgetLineInline, RewardInline, PayoutInline, MessageAdminInline)

    base_model = Funding
    form = FundingAdminForm
    date_hierarchy = 'transition_date'
    list_filter = [StateMachineFilter, CurrencyFilter]

    search_fields = ['title', 'slug', 'description']
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['bank_account']

    basic_fields = ActivityChildAdmin.basic_fields[0:ActivityChildAdmin.basic_fields.index('updated') + 1] + \
        ('started',) + ActivityChildAdmin.basic_fields[ActivityChildAdmin.basic_fields.index('updated') + 1:]

    readonly_fields = ActivityChildAdmin.readonly_fields + [
        'amount_donated', 'amount_raised',
        'donations_link', 'started',
    ]

    list_display = [
        '__str__', 'initiative', 'created', 'state_name',
        'highlight', 'deadline', 'percentage_donated', 'percentage_matching'

    ]

    def percentage_donated(self, obj):
        if obj.target and obj.target.amount and obj.amount_donated.amount:
            return '{:.2f}%'.format((old_div(obj.amount_donated.amount, obj.target.amount)) * 100)
        else:
            return '0%'
    percentage_donated.short_description = _('% donated')

    def percentage_matching(self, obj):
        if obj.amount_matching and obj.amount_matching.amount:
            return '{:.2f}%'.format((old_div(obj.amount_matching.amount, obj.target.amount)) * 100)
        else:
            return '0%'
    percentage_matching.short_description = _('% matching')

    def amount_raised(self, obj):
        return obj.amount_raised
    amount_raised.short_description = _('amount donated + matched')

    def amount_donated(self, obj):
        return obj.amount_donated
    amount_donated.short_description = _('amount donated')

    detail_fields = (
        'description',
        'duration',
        'deadline',
        'target',
        'amount_matching',
        'amount_donated',
        'amount_raised',
        'donations_link',
        'bank_account',
        'highlight',
    )

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('deadline', 'Deadline'),
        ('duration', 'Duration'),
        ('target', 'Target'),
        ('country', 'Country'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('amount_matching', 'Amount Matching'),
        ('bank_account', 'Bank Account'),
        ('amount_donated', 'Amount Donatated'),
        ('amount_raised', 'Amount Raised'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def donations_link(self, obj):
        url = reverse('admin:funding_donation_changelist')
        total = obj.donations.filter(status=DonationStateMachine.succeeded.value).count()
        return format_html('<a href="{}?activity_id={}">{} {}</a>'.format(url, obj.id, total, _('donations')))
    donations_link.short_description = _("Donations")


class DonationAdminForm(StateMachineModelForm):
    class Meta(object):
        model = Donation
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(DonationAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            if self.instance.id:
                # You can only select a reward if the project is set on the donation
                self.fields['reward'].queryset = Reward.objects.filter(activity=self.instance.activity)
            else:
                self.fields['reward'].queryset = Reward.objects.none()


@admin.register(Donation)
class DonationAdmin(ContributionChildAdmin, PaymentLinkMixin):
    model = Donation
    form = DonationAdminForm

    raw_id_fields = ['activity', 'payout', 'user']
    readonly_fields = ContributionChildAdmin.readonly_fields + [
        'payment_link', 'payment_link', 'payout_amount',
    ]
    list_display = ['contribution_date', 'payment_link', 'activity_link', 'user_link', 'state_name', 'amount', ]
    list_filter = [
        DonationAdminStatusFilter,
        DonationAdminCurrencyFilter,
        DonationAdminPledgeFilter,
    ]
    date_hierarchy = 'contribution_date'

    inlines = [DonationWallpostInline]

    superadmin_fields = [
        'force_status',
        'amount'
    ]

    fields = [
        'contribution_date', 'created',
        'activity', 'payout', 'user', 'payout_amount',
        'reward', 'anonymous', 'name', 'status', 'payment_link'
    ]

    export_to_csv_fields = (
        ('status', 'Status'),
        ('created', 'Created'),
        ('activity', 'Activity'),
        ('user__full_name', 'Owner'),
        ('user__email', 'Email'),
        ('amount', 'Amount'),
        ('reward', 'Reward'),
        ('fundraiser', 'Fundraiser'),
        ('name', 'name'),
        ('anonymous', 'Anonymous'),
        ('contribution_date', 'Contribution Date'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def user_link(self, obj):
        if obj.anonymous:
            return format_html('<i style="color: #999">anonymous</i>')
        if obj.user:
            user_url = reverse('admin:members_member_change', args=(obj.user.id,))
            return format_html(u'<a href="{}">{}</a>', user_url, obj.user.full_name)
        return format_html('<i style="color: #999">guest</i>')

    user_link.short_description = _('User')

    def get_changelist(self, request, **kwargs):
        self.total_column = 'amount'
        return TotalAmountAdminChangeList


class PaymentChildAdmin(PolymorphicChildModelAdmin, StateMachineAdmin):
    model = Funding

    raw_id_fields = ['donation']
    change_form_template = 'admin/funding/payment/change_form.html'

    readonly_fields = ['status', 'created', 'updated']
    fields = ['donation', 'states'] + readonly_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Basic'), {'fields': self.get_fields(request, obj)}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': ['force_status']}),
            )
        return fieldsets

    def get_urls(self):
        urls = super(PaymentChildAdmin, self).get_urls()
        process_urls = [
            url(r'^(?P<pk>\d+)/check/$', self.check_status, name="funding_payment_check"),
            url(r'^(?P<pk>\d+)/refund/$', self.refund, name="funding_payment_refund"),
        ]
        return process_urls + urls

    def check_status(self, request, pk=None):
        payment = Payment.objects.get(pk=pk)
        try:
            payment.update()
        except PaymentException as e:
            self.message_user(
                request,
                'Error checking status {}'.format(e),
                level='WARNING'
            )
        payment_url = reverse('admin:{}_{}_change'.format(
            payment._meta.app_label, payment._meta.model_name,
        ), args=(payment.id,))
        response = HttpResponseRedirect(payment_url)
        return response

    @confirmation_form(
        RefundConfirmationForm,
        Payment,
        'admin/payments/refund_confirmation.html'
    )
    def refund(self, request, val=None):
        if isinstance(val, Payment):
            payment = val
        else:
            payment = Payment.objects.get(pk=val)
        try:
            payment.states.request_refund(save=True)
        except PaymentException as e:
            self.message_user(
                request,
                'Error checking status {}'.format(e),
                level='WARNING'
            )
        payment_url = reverse('admin:funding_payment_change', args=(payment.id,))
        response = HttpResponseRedirect(payment_url)
        return response


@admin.register(LegacyPayment)
class LegacyPaymentPaymentAdmin(PaymentChildAdmin):
    base_model = LegacyPayment
    show_in_index = True


@admin.register(Payment)
class PaymentAdmin(PolymorphicParentModelAdmin):
    base_model = Payment
    list_filter = (PolymorphicChildModelFilter, 'status')

    list_display = ('created', 'type', 'status')

    def type(self, obj):
        return obj.get_real_instance_class().__name__

    child_models = (
        StripeSourcePayment,
        StripePayment,
        FlutterwavePayment,
        LipishaPayment,
        VitepayPayment,
        TelesomPayment,
        LegacyPayment,
        PledgePayment
    )


class PaymentCurrencyInline(admin.TabularInline):
    model = PaymentCurrency
    extra = 0

    formfield_overrides = {
        models.CharField: {'widget': forms.TextInput(attrs={'class': 'vIntegerField'})},
        models.DecimalField: {'widget': forms.TextInput(attrs={'class': 'vIntegerField'})},
    }


class PaymentProviderChildAdmin(PolymorphicChildModelAdmin):
    inlines = [PaymentCurrencyInline]
    show_in_index = True

    def get_fieldsets(self, request, obj=None):
        provider = self.model._meta.verbose_name
        return (
            (provider, {
                'fields': self.get_fields(request, obj),
            }),
        )


@admin.register(PaymentProvider)
class PaymentProviderAdmin(PolymorphicParentModelAdmin):
    base_model = PaymentProvider

    child_models = (
        PledgePaymentProvider,
        StripePaymentProvider,
        VitepayPaymentProvider,
        FlutterwavePaymentProvider,
        TelesomPaymentProvider,
        LipishaPaymentProvider
    )


class PayoutAccountFundingLinkMixin(object):
    def funding_links(self, obj):
        if len(obj.funding_set.all()):
            return format_html(", ".join([
                format_html(
                    u"<a href='{}'>{}</a>",
                    reverse('admin:funding_funding_change', args=(p.id,)),
                    p.title
                ) for p in obj.funding_set.all()
            ]))
        else:
            return _('None')

    funding_links.short_description = _('Funding activities')


class PayoutAccountChildAdmin(PolymorphicChildModelAdmin, StateMachineAdmin):
    base_model = PayoutAccount
    raw_id_fields = ('owner',)
    readonly_fields = ['status', 'created']
    fields = ['owner', 'status', 'created', 'reviewed']
    show_in_index = True

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Basic'), {'fields': self.get_fields(request, obj)}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': ['force_status']}),
            )
        return fieldsets


@admin.register(PayoutAccount)
class PayoutAccountAdmin(PolymorphicParentModelAdmin):
    base_model = PayoutAccount
    list_display = ('created', 'polymorphic_ctype', 'reviewed', 'owner',)
    list_filter = ('reviewed', PolymorphicChildModelFilter)
    raw_id_fields = ('owner',)
    show_in_index = True
    search_fields = ['stripepayoutaccount__account_id']
    ordering = ('-created',)
    child_models = [
        StripePayoutAccount,
        PlainPayoutAccount
    ]


class BankAccountChildAdmin(PayoutAccountFundingLinkMixin, PolymorphicChildModelAdmin):
    base_model = BankAccount
    raw_id_fields = ('connect_account',)
    readonly_fields = ('verified', 'funding_links', 'created', 'updated')
    fields = ('connect_account', 'reviewed', ) + readonly_fields
    show_in_index = True

    def get_form(self, request, obj=None, **kwargs):
        help_texts = {
            'verified': _('To verify this bank account review details here and also review the connected account.')
        }
        kwargs.update({'help_texts': help_texts})
        return super(BankAccountChildAdmin, self).get_form(request, obj, **kwargs)


@admin.register(BankAccount)
class BankAccountAdmin(PayoutAccountFundingLinkMixin, PolymorphicParentModelAdmin):
    base_model = BankAccount
    list_display = ('created', 'polymorphic_ctype', 'reviewed', 'funding_links')
    list_filter = ('reviewed', PolymorphicChildModelFilter)
    raw_id_fields = ('connect_account',)
    show_in_index = True
    search_fields = ['externalaccount__account_id',
                     'flutterwavebankaccount__account_holder_name',
                     'pledgebankaccount__account_holder_name',
                     ]

    ordering = ('-created',)
    child_models = [
        ExternalAccount,
        FlutterwaveBankAccount,
        LipishaBankAccount,
        VitepayBankAccount,
        PledgeBankAccount,
    ]


class BankAccountInline(TabularInline):
    model = BankAccount
    readonly_fields = ('link', 'created', 'reviewed')
    fields = readonly_fields
    extra = 0
    can_delete = False

    def link(self, obj):
        url = reverse('admin:funding_bankaccount_change', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', url, obj)


@admin.register(PlainPayoutAccount)
class PlainPayoutAccountAdmin(PayoutAccountChildAdmin):
    model = PlainPayoutAccount
    inlines = [BankAccountInline]
    fields = PayoutAccountChildAdmin.fields + ['document']


class DonationInline(PaymentLinkMixin, admin.TabularInline):
    model = Donation
    readonly_fields = ('created', 'amount', 'status', 'payment_link')
    fields = readonly_fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request):
        return False


@admin.register(Payout)
class PayoutAdmin(StateMachineAdmin):
    model = Payout
    inlines = [DonationInline]
    raw_id_fields = ('activity', )
    readonly_fields = [
        'status',
        'total_amount',
        'account_link',
        'currency',
        'provider',
        'date_approved',
        'date_started',
        'date_completed'
    ]
    list_display = ['created', 'activity_link', 'status']
    list_filter = ['status']

    fields = [
        'activity',
        'states',
    ] + readonly_fields

    def account_link(self, obj):
        url = reverse('admin:funding_bankaccount_change', args=(obj.activity.bank_account.id,))
        return format_html(u'<a href="{}">{}</a>', url, obj.activity.bank_account)

    def activity_link(self, obj):
        url = reverse('admin:funding_funding_change', args=(obj.activity.id,))
        return format_html(u'<a href="{}">{}</a>', url, obj.activity)

    def get_fieldsets(self, request, obj=None):
        fieldsets = (
            (_('Basic'), {'fields': self.get_fields(request, obj)}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': ['force_status']}),
            )
        return fieldsets


@admin.register(FundingPlatformSettings)
class FundingPlatformSettingsAdmin(BasePlatformSettingsAdmin):
    pass
