import logging

from babel.numbers import get_currency_symbol
from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin import TabularInline, SimpleListFilter
from django.db import models
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import PolymorphicChildModelAdmin
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic.admin.parentadmin import PolymorphicParentModelAdmin

from bluebottle.activities.admin import ActivityChildAdmin, ContributionChildAdmin
from bluebottle.activities.transitions import ActivityReviewTransitions
from bluebottle.bluebottle_dashboard.decorators import confirmation_form
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.filters import DonationAdminStatusFilter, DonationAdminCurrencyFilter
from bluebottle.funding.forms import RefundConfirmationForm
from bluebottle.funding.models import (
    Funding, Donation, Payment, PaymentProvider,
    BudgetLine, PayoutAccount, LegacyPayment, BankAccount, PaymentCurrency, PlainPayoutAccount, Payout, Reward)
from bluebottle.funding.transitions import DonationTransitions, FundingTransitions
from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider, FlutterwaveBankAccount, \
    FlutterwavePayment
from bluebottle.funding_lipisha.models import LipishaPaymentProvider, LipishaBankAccount, LipishaPayment
from bluebottle.funding_pledge.models import PledgePayment, PledgePaymentProvider, PledgeBankAccount
from bluebottle.funding_stripe.models import StripePaymentProvider, StripePayoutAccount, \
    StripeSourcePayment, ExternalAccount
from bluebottle.funding_vitepay.models import VitepayPaymentProvider, VitepayBankAccount, VitepayPayment
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import FSMAdmin, TotalAmountAdminChangeList, export_as_csv_action, FSMAdminMixin

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

    extra = 0


class RewardInline(admin.TabularInline):
    model = Reward
    readonly_fields = ('link', 'amount', 'description', 'limit')
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


class FundingStatusFilter(SimpleListFilter):

    title = _('Status')
    parameter_name = 'status'

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                Q(status=self.value()) |
                Q(review_status=self.value()))
        return queryset

    def lookups(self, request, model_admin):
        return ActivityReviewTransitions.values.choices + FundingTransitions.values.choices


class PayoutInline(FSMAdminMixin, admin.StackedInline):

    model = Payout
    readonly_fields = [
        'total_amount', 'date_approved', 'date_started', 'date_completed',
        'status', 'approve'
    ]

    fields = readonly_fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request):
        return False

    def approve(self, obj):
        if obj.status == 'new':
            url = reverse('admin:funding_payout_transition', args=(obj.id, 'transitions', 'approve'))
            return format_html('<a href="{}">{}</a>', url, _('Approve'))


@admin.register(Funding)
class FundingAdmin(ActivityChildAdmin):
    inlines = (BudgetLineInline, RewardInline, PayoutInline, MessageAdminInline)
    base_model = Funding
    date_hierarchy = 'deadline'
    list_filter = [FundingStatusFilter, CurrencyFilter]

    search_fields = ['title', 'slug', 'description']
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['bank_account']

    readonly_fields = ActivityChildAdmin.readonly_fields + [
        'amount_donated', 'amount_raised',
        'donations_link', 'payout_links'
    ]

    list_display = [
        '__unicode__', 'initiative', 'created', 'combined_status',
        'highlight', 'deadline', 'target', 'amount_raised'
    ]

    def amount_raised(self, obj):
        return obj.amount_raised
    amount_raised.short_description = _('amount donated + matched')

    def amount_donated(self, obj):
        return obj.amount_raised
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
        'payout_links'
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
        ('owner', 'Owner'),
        ('amount_matching', 'Amount Matching'),
        ('bank_account', 'Bank Account'),
        ('amount_donated', 'Amount Donatated'),
        ('amount_raised', 'Amount Raised'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def donations_link(self, obj):
        url = reverse('admin:funding_donation_changelist')
        total = obj.contributions.filter(status=DonationTransitions.values.succeeded).count()
        return format_html('<a href="{}?activity_id={}">{} {}</a>'.format(url, obj.id, total, _('donations')))
    donations_link.short_description = _("Donations")

    def payout_links(self, obj):
        return format_html(", ".join([
            format_html(
                u"<a href='{}'>{}</a>",
                reverse('admin:funding_payout_change', args=(p.id,)),
                p.id
            ) for p in obj.payouts.all()
        ]))

    payout_links.short_description = _('Payouts')

    def combined_status(self, obj):
        if obj.status == 'in_review':
            return obj.review_status
        return obj.status
    combined_status.short_description = _('status')


@admin.register(Donation)
class DonationAdmin(ContributionChildAdmin, PaymentLinkMixin):
    model = Donation
    raw_id_fields = ['activity', 'user']
    readonly_fields = ['payment_link', 'status', 'payment_link']
    list_display = ['created', 'payment_link', 'activity_link', 'user_link', 'status', 'amount', ]
    list_filter = [DonationAdminStatusFilter, DonationAdminCurrencyFilter]
    date_hierarchy = 'created'

    export_to_csv_fields = (
        ('status', 'Status'),
        ('created', 'Created'),
        ('activity', 'Activity'),
        ('owner', 'Owner'),
        ('amount', 'Amount'),
        ('reward', 'Reward'),
        ('fundraiser', 'Fundraiser'),
        ('name', 'name'),
        ('anonymous', 'Anonymous'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def user_link(self, obj):
        # if obj.anonymous:
        #     format_html('<i style="color: #999">anonymous</i>')
        if obj.user:
            user_url = reverse('admin:funding_funding_change', args=(obj.user.id,))
            return format_html(u'<a href="{}">{}</a>', user_url, obj.user.full_name)
        return format_html('<i style="color: #999">guest</i>')

    user_link.short_description = _('User')

    def get_changelist(self, request, **kwargs):
        self.total_column = 'amount'
        return TotalAmountAdminChangeList

    fields = ['created', 'activity', 'user', 'amount', 'status', 'payment_link']


class PaymentChildAdmin(PolymorphicChildModelAdmin, FSMAdmin):
    model = Funding

    raw_id_fields = ['donation']
    change_form_template = 'admin/funding/payment/change_form.html'

    def get_fields(self, request, obj=None):
        fields = super(PaymentChildAdmin, self).get_fields(request, obj)
        # Don't show
        if not request.user.is_superuser:
            fields.remove('transitions')
        return fields

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
            payment.transitions.request_refund()
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
        FlutterwavePayment,
        LipishaPayment,
        VitepayPayment,
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
        LipishaPaymentProvider
    )


class PayoutAccountFundingLinkMixin(object):
    def funding_links(self, obj):
        return format_html(", ".join([
            format_html(
                u"<a href='{}'>{}</a>",
                reverse('admin:funding_funding_change', args=(p.id,)),
                p.title
            ) for p in obj.funding_set.all()
        ]))

    funding_links.short_description = _('Funding activities')


class PayoutAccountChildAdmin(PolymorphicChildModelAdmin, FSMAdmin):
    base_model = PayoutAccount
    raw_id_fields = ('owner',)
    readonly_fields = ('status',)
    fields = ('owner', 'status', 'transitions')
    show_in_index = True


@admin.register(PayoutAccount)
class PayoutAccountAdmin(PolymorphicParentModelAdmin):
    base_model = PayoutAccount
    list_display = ('created', 'polymorphic_ctype', 'reviewed',)
    list_filter = ('reviewed', PolymorphicChildModelFilter)
    raw_id_fields = ('owner',)
    show_in_index = True

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


@admin.register(BankAccount)
class BankAccountAdmin(PayoutAccountFundingLinkMixin, PolymorphicParentModelAdmin):
    base_model = BankAccount
    list_display = ('created', 'polymorphic_ctype', 'reviewed', 'funding_links')
    list_filter = ('reviewed', PolymorphicChildModelFilter)
    raw_id_fields = ('connect_account',)
    show_in_index = True

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

    fields = PayoutAccountChildAdmin.fields + ('document',)


class DonationInline(admin.TabularInline):
    model = Donation
    readonly_fields = ('created', 'amount', 'status')
    fields = readonly_fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request):
        return False


@admin.register(Payout)
class PayoutAdmin(FSMAdmin):
    model = Payout
    inlines = [DonationInline]
    raw_id_fields = ('activity', )
    readonly_fields = ['activity_link', 'status', 'total_amount',
                       'date_approved', 'date_started', 'date_completed']
    list_display = ['created', 'activity_link', 'status']

    def activity_link(self, obj):
        url = reverse('admin:funding_funding_change', args=(obj.activity.id,))
        return format_html(u'<a href="{}">{}</a>', url, obj.activity)
