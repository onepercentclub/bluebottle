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
from bluebottle.funding.filters import DonationAdminStatusFilter
from bluebottle.funding.models import (
    Funding, Donation, Payment, PaymentProvider,
    BudgetLine, PayoutAccount, BankPayoutAccount, BankPaymentProvider, LegacyPayment)
from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider, FlutterwavePayoutAccount, \
    FlutterwavePayment
from bluebottle.funding_lipisha.models import LipishaPaymentProvider, LipishaPayoutAccount
from bluebottle.funding_pledge.models import PledgePayment, PledgePaymentProvider
from bluebottle.funding_stripe.models import StripePaymentProvider, StripePayoutAccount, \
    StripeSourcePayment
from bluebottle.funding_vitepay.models import VitepayPaymentProvider, VitepayPayoutAccount
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


class PayoutAccountChildAdmin(PayoutAccountFundingLinkMixin, PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    raw_id_fields = ('owner',)
    readonly_fields = ('status', 'funding_links')
    fields = ('owner', 'status', 'funding_links')


@admin.register(PayoutAccount)
class PayoutAccountAdmin(PayoutAccountFundingLinkMixin, PolymorphicParentModelAdmin):
    base_model = PayoutAccount
    list_display = ('created', 'polymorphic_ctype', 'reviewed', 'funding_links')
    list_filter = ('reviewed', PolymorphicChildModelFilter)
    readonly_fields = ('funding_links',)
    raw_id_fields = ('owner',)

    ordering = ('-created',)
    child_models = [
        StripePayoutAccount,
        FlutterwavePayoutAccount,
        LipishaPayoutAccount,
        VitepayPayoutAccount,
        BankPayoutAccount
    ]


@admin.register(BankPayoutAccount)
class BankPayoutAccountAdmin(PayoutAccountFundingLinkMixin, PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = BankPayoutAccount
    raw_id_fields = ('owner',)
    fields = ('owner', 'account_holder_name', 'bank_country', 'account_number')


class DonationInline(admin.TabularInline, PaymentLinkMixin):
    model = Donation

    raw_id_fields = ('user',)
    readonly_fields = ('donation', 'user', 'amount', 'status', 'payment_link')
    fields = readonly_fields
    extra = 0

    def donation(self, obj):
        url = reverse('admin:funding_donation_change', args=(obj.id,))
        return format_html('<a href="{}">{} {}</a>',
                           url,
                           obj.created.date(),
                           obj.created.strftime('%H:%M'))


class BudgetLineInline(admin.TabularInline):
    model = BudgetLine

    extra = 0


@admin.register(Funding)
class FundingAdmin(ActivityChildAdmin):
    inlines = (BudgetLineInline, DonationInline, MessageAdminInline)
    base_model = Funding

    search_fields = ['title', 'slug', 'description']

    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['account']

    readonly_fields = ActivityChildAdmin.readonly_fields + ['amount_donated', 'amount_raised']

    list_display = ['title_display', 'initiative', 'status', 'deadline', 'target', 'amount_raised']

    fieldsets = (
        (_('Basic'), {'fields': (
            'title', 'slug', 'initiative', 'owner', 'status', 'transitions', 'created', 'updated', 'highlight'
        )}),
        (_('Details'), {'fields': (
            'description',
            'duration',
            'deadline',
            'target',
            'amount_matching',
            'amount_donated',
            'amount_raised',
            'account'
        )}),
    )


@admin.register(Donation)
class DonationAdmin(FSMAdmin, PaymentLinkMixin):
    raw_id_fields = ['activity', 'user']
    readonly_fields = ['payment_link', 'status', 'user_full_name']
    model = Donation
    list_display = ['created', 'payment_link', 'user_full_name', 'status', 'amount']
    list_filter = [DonationAdminStatusFilter, 'amount_currency']
    date_hierarchy = 'created'

    def user_full_name(self, obj):
        # if obj.anonymous:
        #     format_html('<i style="color: #999">anonymous</i>')
        if obj.user:
            return obj.user.full_name
        return format_html('<i style="color: #999">guest</i>')

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
