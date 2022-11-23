from __future__ import division

import logging
from builtins import object
from datetime import timedelta

from babel.numbers import get_currency_symbol
from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin import TabularInline, SimpleListFilter
from django.db import models, connection
from django.forms.utils import ErrorList
from django.http import HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django_summernote.widgets import SummernoteWidget
from past.utils import old_div
from polymorphic.admin import PolymorphicChildModelAdmin
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic.admin.parentadmin import PolymorphicParentModelAdmin

from bluebottle.activities.admin import ActivityChildAdmin, ContributorChildAdmin, ContributionChildAdmin, ActivityForm
from bluebottle.bluebottle_dashboard.decorators import confirmation_form
from bluebottle.fsm.admin import StateMachineAdmin, StateMachineAdminMixin, StateMachineFilter
from bluebottle.fsm.forms import StateMachineModelForm
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.filters import DonorAdminStatusFilter, DonorAdminCurrencyFilter, DonorAdminPledgeFilter
from bluebottle.funding.forms import RefundConfirmationForm
from bluebottle.funding.models import (
    Funding, Donor, Payment, PaymentProvider,
    BudgetLine, PayoutAccount, LegacyPayment, BankAccount, PaymentCurrency, PlainPayoutAccount, Payout, Reward,
    FundingPlatformSettings, MoneyContribution)
from bluebottle.funding.states import DonorStateMachine
from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider, FlutterwaveBankAccount, \
    FlutterwavePayment
from bluebottle.funding_lipisha.models import LipishaPaymentProvider, LipishaBankAccount, LipishaPayment
from bluebottle.funding_pledge.models import PledgePayment, PledgePaymentProvider, PledgeBankAccount
from bluebottle.funding_stripe.models import StripePaymentProvider, StripePayoutAccount, \
    StripeSourcePayment, ExternalAccount, StripePayment
from bluebottle.funding_telesom.models import TelesomPaymentProvider, TelesomPayment, TelesomBankAccount
from bluebottle.funding_vitepay.models import VitepayPaymentProvider, VitepayBankAccount, VitepayPayment
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import TotalAmountAdminChangeList, export_as_csv_action, BasePlatformSettingsAdmin
from bluebottle.utils.utils import reverse_signed
from bluebottle.wallposts.admin import DonorWallpostInline

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
    readonly_fields = ('link', 'description', 'created')
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

    def has_add_permission(self, request, obj=None):
        return False

    def payout_link(self, obj):
        url = reverse('admin:funding_payout_change', args=(obj.id, ))
        return format_html(u'<a href="{}">{}</a>', url, obj)


class FundingAdminForm(ActivityForm):

    def clean(self):
        clean = super(FundingAdminForm, self).clean()
        donation = self.instance.donations.filter(status='succeeded').order_by('created').first()
        if donation and clean['deadline'] > donation.created + timedelta(days=61):
            message = str(_("Can't extend a deadline to more then 60 days from the first donation, which was {date}. "
                            "Maximum deadline is {deadline}"))
            message = message.format(
                date=str(donation.created.date()),
                deadline=str(donation.created.date() + timedelta(days=60)),
            )
            self.errors['deadline'] = ErrorList([message])
        return clean

    class Meta(object):
        model = Funding
        fields = '__all__'
        widgets = {
            'description': SummernoteWidget(attrs={'height': 400})
        }


@admin.register(Funding)
class FundingAdmin(ActivityChildAdmin):
    inlines = (BudgetLineInline, RewardInline, PayoutInline, MessageAdminInline)

    base_model = Funding
    form = FundingAdminForm
    list_filter = [StateMachineFilter, CurrencyFilter]

    search_fields = ['title', 'slug', 'description']
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['bank_account']

    detail_fields = ActivityChildAdmin.detail_fields + (
        'started',
        'duration',
        'deadline',
        'target',
        'amount_matching',
        'amount_donated',
        'amount_raised',
        'donors_link',
        'bank_account',
    )

    readonly_fields = ActivityChildAdmin.readonly_fields + [
        'amount_donated', 'amount_raised',
        'donors_link', 'started', 'team_activity'
    ]

    list_display = ActivityChildAdmin.list_display + [
        'deadline', 'percentage_donated', 'percentage_matching'

    ]

    def percentage_donated(self, obj):
        if obj.target and obj.target.amount and obj.amount_donated.amount:
            return '{:.2f}%'.format((old_div(obj.amount_donated.amount, obj.target.amount)) * 100)
        else:
            return '0%'
    # Translators: xgettext:no-python-format
    percentage_donated.short_description = _('% donated')

    def percentage_matching(self, obj):
        if obj.amount_matching and obj.amount_matching.amount:
            return '{:.2f}%'.format((old_div(obj.amount_matching.amount, obj.target.amount)) * 100)
        else:
            return '0%'
    # Translators: xgettext:no-python-format
    percentage_matching.short_description = _('% matching')

    def amount_raised(self, obj):
        return obj.amount_raised
    amount_raised.short_description = _('amount donated + matched')

    def amount_donated(self, obj):
        return obj.amount_donated
    amount_donated.short_description = _('amount donated')

    export_to_csv_fields = (
        ('title', 'Title'),
        ('description', 'Description'),
        ('status', 'Status'),
        ('created', 'Created'),
        ('initiative__title', 'Initiative'),
        ('deadline', 'Deadline'),
        ('target', 'Target'),
        ('country', 'Country'),
        ('owner__full_name', 'Owner'),
        ('owner__email', 'Email'),
        ('amount_matching', 'Amount Matching'),
        ('bank_account', 'Bank Account'),
        ('office_location', 'Office Location'),
        ('amount_donated', 'Amount Donatated'),
        ('amount_raised', 'Amount Raised'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

    def donors_link(self, obj):
        url = reverse('admin:funding_donor_changelist')
        total = obj.donations.filter(status=DonorStateMachine.succeeded.value).count()
        return format_html('<a href="{}?activity_id={}">{} {}</a>'.format(url, obj.id, total, _('donations')))
    donors_link.short_description = _("Donations")


class DonorAdminForm(StateMachineModelForm):
    class Meta(object):
        model = Donor
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(DonorAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            if self.instance.id:
                # You can only select a reward if the project is set on the donation
                self.fields['reward'].queryset = Reward.objects.filter(activity=self.instance.activity)
            else:
                self.fields['reward'].queryset = Reward.objects.none()


class MoneyContributionInlineAdmin(admin.StackedInline):
    model = MoneyContribution
    extra = 0
    readonly_fields = ('status', 'created', 'value')


@admin.register(MoneyContribution)
class MoneyContributionAdmin(ContributionChildAdmin):
    model = MoneyContribution

    fields = ContributionChildAdmin.fields + ['value']


@admin.register(Donor)
class DonorAdmin(ContributorChildAdmin, PaymentLinkMixin):
    model = Donor
    form = DonorAdminForm

    raw_id_fields = ['activity', 'payout', 'user']
    readonly_fields = ContributorChildAdmin.readonly_fields + [
        'amount_value', 'payout_amount_value',
        'payment_link', 'sync_payment_link'
    ]
    list_display = ['created', 'payment_link', 'activity_link', 'user_link',
                    'state_name', 'amount', 'payout_amount']
    list_filter = [
        DonorAdminStatusFilter,
        DonorAdminCurrencyFilter,
        DonorAdminPledgeFilter,
    ]
    date_hierarchy = 'created'

    inlines = [
        DonorWallpostInline
    ]

    superadmin_fields = [
        'force_status',
        'amount',
        'payout_amount',
        'sync_payment_link'
    ]

    fields = [
        'created', 'activity', 'payout', 'user',
        'amount_value', 'payout_amount_value',
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
        ('id', 'Order ID'),
    )

    def get_exclude(self, request, obj=None):
        if not request.user.is_superuser:
            return ('amount', 'payout_amount', )
        else:
            return []

    def amount_value(self, obj):
        if obj:
            return obj.amount
    amount_value.short_description = _('Amount')

    def payout_amount_value(self, obj):
        if obj:
            return obj.payout_amount
    payout_amount_value.short_description = _('Payout amount')

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

    def get_urls(self):
        urls = super(StateMachineAdminMixin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<pk>.+)/sync/$',
                self.admin_site.admin_view(self.sync_payment),
                name='funding_donation_sync',
            )
        ]
        return custom_urls + urls

    def sync_payment(self, request, pk=None):
        donor = Donor.objects.get(pk=pk)
        if str(donor.amount.currency) == 'NGN':
            try:
                donor.payment
            except Payment.DoesNotExist:
                payment = FlutterwavePayment.objects.create(
                    donation=donor,
                    tx_ref=donor.pk
                )
                payment.save()
                self.message_user(
                    request,
                    'Generated missing payment',
                    level='SUCCESS'
                )
            donor.payment.update()
            self.message_user(
                request,
                'Checked payment status for {}'.format(donor.payment),
                level='INFO'
            )
        else:
            try:
                if donor.payment.update:
                    donor.payment.update()
                    self.message_user(
                        request,
                        'Checked payment status for {}'.format(donor.payment),
                        level='INFO'
                    )
                else:
                    self.message_user(
                        request,
                        'Warning cannot check status for {}'.format(donor.payment),
                        level='INFO'
                    )
            except Payment.DoesNotExist:
                self.message_user(
                    request,
                    'Payment not found',
                    level='WARNING'
                )

        donor_url = reverse('admin:funding_donor_change', args=(donor.id,))
        response = HttpResponseRedirect(donor_url)
        return response

    def sync_payment_link(self, obj):
        sync_url = reverse('admin:funding_donation_sync', args=(obj.id,))
        return format_html('<a href="{}">{}</a>', sync_url, _('Sync donation with payment.'))


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
    search_fields = [
        'stripepayoutaccount__account_id',
        'owner__first_name', 'owner__last_name', 'owner__email'
    ]
    ordering = ('-created',)
    child_models = [
        StripePayoutAccount,
        PlainPayoutAccount
    ]


class BankAccountChildAdmin(StateMachineAdminMixin, PayoutAccountFundingLinkMixin, PolymorphicChildModelAdmin):
    base_model = BankAccount
    raw_id_fields = ('connect_account',)
    readonly_fields = ('document', 'funding_links', 'created', 'updated')
    fields = ('funding_links', 'connect_account', 'document', 'status', 'states', 'created', 'updated')
    show_in_index = True

    def document(self, obj):
        if obj.connect_account and \
                isinstance(obj.connect_account, PlainPayoutAccount) and \
                obj.connect_account.document and \
                obj.connect_account.document.file:
            template = loader.get_template(
                'admin/document_button.html'
            )
            if 'localhost' in connection.tenant.domain_url:
                download_url = obj.connect_account.document.file.url
            else:
                download_url = reverse_signed('kyc-document', args=(obj.connect_account.id,))
            return template.render({'document_url': download_url})
        return "_"


@admin.register(BankAccount)
class BankAccountAdmin(PayoutAccountFundingLinkMixin, PolymorphicParentModelAdmin):
    base_model = BankAccount
    list_display = ('created', 'polymorphic_ctype', 'status', 'funding_links')
    list_filter = ('status', PolymorphicChildModelFilter)
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
        TelesomBankAccount
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
    readonly_fields = ['document_link']
    fields = PayoutAccountChildAdmin.fields + ['document', 'document_link']

    def document_link(self, obj):
        if obj.document and obj.document.file:
            template = loader.get_template(
                'admin/document_button.html'
            )
            if 'localhost' in connection.tenant.domain_url:
                download_url = obj.document.file.url
            else:
                download_url = reverse_signed('kyc-document', args=(obj.id,))
            return template.render({'document_url': download_url})
        return "_"


class DonorInline(PaymentLinkMixin, admin.TabularInline):
    model = Donor
    readonly_fields = ('created', 'amount', 'status', 'payment_link')
    fields = readonly_fields
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Payout)
class PayoutAdmin(StateMachineAdmin):
    model = Payout
    inlines = [DonorInline]
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

    export_to_csv_fields = (
        ('id', 'Id'),
        ('status', 'Status'),
        ('date_started', 'date_started'),
        ('date_approved', 'date_approved'),
        ('activity__title', 'Activity'),
        ('activity__initiative__title', 'Initiative'),
        ('total_amount', 'Amount'),
        ('currency', 'Currency'),
        ('provider', 'Provider'),
    )

    actions = [export_as_csv_action(fields=export_to_csv_fields)]

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
