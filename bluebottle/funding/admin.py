import logging

from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import PolymorphicChildModelAdmin
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic.admin.parentadmin import PolymorphicParentModelAdmin

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.filters import DonationAdminStatusFilter, DonationAdminCurrencyFilter
from bluebottle.funding.models import (
    Funding, Donation, Payment, PaymentProvider,
    BudgetLine, PayoutAccount, PlainBankAccount, BankPaymentProvider, LegacyPayment, BankAccount)
from bluebottle.funding.transitions import DonationTransitions
from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider, FlutterwaveBankAccount, \
    FlutterwavePayment
from bluebottle.funding_lipisha.models import LipishaPaymentProvider, LipishaBankAccount
from bluebottle.funding_pledge.models import PledgePayment, PledgePaymentProvider
from bluebottle.funding_stripe.models import StripePaymentProvider, StripePayoutAccount, \
    StripeSourcePayment, ExternalAccount
from bluebottle.funding_vitepay.models import VitepayPaymentProvider, VitepayBankAccount
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import FSMAdmin, TotalAmountAdminChangeList

logger = logging.getLogger(__name__)


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


class PaymentLinkMixin(object):

    def payment_link(self, obj):
        payment_url = reverse('admin:{}_{}_change'.format(
            obj.payment._meta.app_label, obj.payment._meta.model_name,
        ), args=(obj.payment.id,))
        return format_html('<a href="{}">{}</a>', payment_url, obj.payment)

    payment_link.short_description = _('Payment')


class PayoutAccountChildAdmin(PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    raw_id_fields = ('owner',)
    readonly_fields = ('status',)
    fields = ('owner', 'status',)


@admin.register(PayoutAccount)
class PayoutAccountAdmin(PolymorphicParentModelAdmin):
    base_model = PayoutAccount
    list_display = ('created', 'polymorphic_ctype', 'reviewed',)
    list_filter = ('reviewed', PolymorphicChildModelFilter)
    raw_id_fields = ('owner',)

    ordering = ('-created',)
    child_models = [
        StripePayoutAccount,
        FlutterwaveBankAccount,
        LipishaBankAccount,
        VitepayBankAccount
    ]


class BankAccountChildAdmin(PayoutAccountFundingLinkMixin, PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    raw_id_fields = ('owner',)
    readonly_fields = ('funding_links',)
    fields = ('owner', 'funding_links')


@admin.register(BankAccount)
class BankAccountAdmin(PayoutAccountFundingLinkMixin, PolymorphicParentModelAdmin):
    base_model = PayoutAccount
    list_display = ('created', 'polymorphic_ctype', 'reviewed', 'funding_links')
    list_filter = ('reviewed', PolymorphicChildModelFilter)
    readonly_fields = ('funding_links',)
    raw_id_fields = ('owner',)

    ordering = ('-created',)
    child_models = [
        ExternalAccount,
        FlutterwaveBankAccount,
    ]


@admin.register(PlainBankAccount)
class PlainBankAccountAdmin(BankAccountChildAdmin):
    base_model = BankAccount
    model = PlainBankAccount
    raw_id_fields = ('owner',)
    readonly_fields = ('funding_links',)
    fields = BankAccountChildAdmin.fields + ('account_holder_name', 'bank_country', 'account_number')


class BudgetLineInline(admin.TabularInline):
    model = BudgetLine

    extra = 0


@admin.register(Funding)
class FundingAdmin(ActivityChildAdmin):
    inlines = (BudgetLineInline, MessageAdminInline)
    base_model = Funding

    search_fields = ['title', 'slug', 'description']
    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['bank_account']

    readonly_fields = ActivityChildAdmin.readonly_fields + ['amount_donated', 'amount_raised', 'donations_link']

    list_display = ['title_display', 'initiative', 'status', 'deadline', 'target', 'amount_raised']

    detail_fields = (
        'description',
        'duration',
        'deadline',
        'target',
        'amount_matching',
        'amount_donated',
        'amount_raised',
        'donations_link',
        'bank_account'
    )

    status_fields = (
        'complete',
        'valid',
        'review_status',
        'review_transitions',
        'status',
        'transitions',
    )

    def donations_link(self, obj):
        url = reverse('admin:funding_donation_changelist')
        total = obj.contributions.filter(status=DonationTransitions.values.succeeded).count()
        return format_html('<a href="{}?activity_id={}">{} {}</a>'.format(url, obj.id, total, _('donations')))

    donations_link.short_description = _("Donations")


@admin.register(Donation)
class DonationAdmin(FSMAdmin, PaymentLinkMixin):
    raw_id_fields = ['activity', 'user']
    readonly_fields = ['payment_link', 'status', 'payment_link', 'funding_link']
    model = Donation
    list_display = ['created', 'payment_link', 'funding_link', 'user_link', 'status', 'amount', 'payout_amount']
    list_filter = [DonationAdminStatusFilter, DonationAdminCurrencyFilter]
    date_hierarchy = 'created'

    def user_link(self, obj):
        # if obj.anonymous:
        #     format_html('<i style="color: #999">anonymous</i>')
        if obj.user:
            user_url = reverse('admin:funding_funding_change', args=(obj.user.id,))
            return format_html(u'<a href="{}">{}</a>', user_url, obj.user.full_name)
        return format_html('<i style="color: #999">guest</i>')

    user_link.short_description = _('User')

    def funding_link(self, obj):
        funding_url = reverse('admin:funding_funding_change', args=(obj.activity.id,))
        return format_html(u'<a href="{}">{}</a>', funding_url, obj.activity.title)

    funding_link.short_description = _('Funding activity')

    def get_changelist(self, request, **kwargs):
        self.total_column = 'amount'
        return TotalAmountAdminChangeList

    fields = ['created', 'activity', 'user', 'amount', 'status', 'payment_link']


class PaymentChildAdmin(PolymorphicChildModelAdmin, FSMAdmin):
    model = Funding

    raw_id_fields = ['donation']
    change_form_template = 'admin/funding/payment/change_form.html'

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

    def refund(self, request, pk=None):
        payment = Payment.objects.get(pk=pk)
        try:
            payment.refund()
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
        LegacyPayment,
        PledgePayment
    )


class PaymentProviderChildAdmin(PolymorphicChildModelAdmin):
    def response_add(self, request, obj, post_url_continue=None):
        return redirect(reverse('admin:funding_paymentprovider_changelist'))

    def response_change(self, request, obj):
        return redirect(reverse('admin:funding_paymentprovider_changelist'))


@admin.register(PaymentProvider)
class PaymentProviderAdmin(PolymorphicParentModelAdmin):
    base_model = PaymentProvider

    child_models = (
        PledgePaymentProvider,
        StripePaymentProvider,
        VitepayPaymentProvider,
        FlutterwavePaymentProvider,
        LipishaPaymentProvider,
        BankPaymentProvider
    )


@admin.register(BankPaymentProvider)
class BankPaymentProviderAdmin(PaymentProviderChildAdmin):
    base_model = BankPaymentProvider
