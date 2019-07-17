from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.models import (
    Funding, Donation, Payment, PaymentProvider,
    BudgetLine)
from bluebottle.funding_flutterwave.models import FlutterwavePaymentProvider
from bluebottle.funding_lipisha.models import LipishaPaymentProvider
from bluebottle.funding_pledge.models import PledgePayment, PledgePaymentProvider
from bluebottle.funding_stripe.models import StripePayment, StripePaymentProvider
from bluebottle.funding_vitepay.models import VitepayPaymentProvider
from bluebottle.notifications.admin import MessageAdminInline
from bluebottle.utils.admin import FSMAdmin


class PaymentLinkMixin(object):

    def payment_link(self, obj):
        url = reverse('admin:funding_payment_change', args=(obj.payment.id,))
        return format_html('<a href="{}">{}</a>', url, obj.payment)

    payment_link.short_description = _('Payment')


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

    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['account']

    readonly_fields = ActivityChildAdmin.readonly_fields + ['amount_donated', 'amount_raised']

    list_display = ['title_display', 'initiative', 'status', 'deadline', 'target', 'amount_raised']

    fieldsets = (
        (_('Basic'), {'fields': (
            'title', 'slug', 'initiative', 'owner', 'status', 'status_transition', 'created', 'updated', 'highlight'
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
    readonly_fields = ['payment_link', 'status']
    model = Donation
    list_display = ['user', 'status', 'amount']

    fields = ['created', 'activity', 'user', 'amount', 'status', 'status_transition', 'payment_link']


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
        payment_url = reverse('admin:funding_payment_change', args=(payment.id,))
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


@admin.register(Payment)
class PaymentAdmin(PolymorphicParentModelAdmin):
    base_model = Payment
    child_models = (StripePayment, PledgePayment)


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
        LipishaPaymentProvider
    )
