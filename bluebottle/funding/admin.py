from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin

from bluebottle.activities.admin import ActivityChildAdmin
from bluebottle.funding.exception import PaymentException
from bluebottle.funding.models import Funding, Donation, Payment
from bluebottle.funding_pledge.models import PledgePayment
from bluebottle.funding_stripe.models import StripePayment
from bluebottle.utils.admin import FSMAdmin


class DonationInline(admin.TabularInline):
    model = Donation

    raw_id_fields = ('user',)
    readonly_fields = ('donation', 'user', 'amount', 'status',)
    fields = readonly_fields
    extra = 0

    def donation(self, obj):
        url = reverse('admin:funding_donation_change', args=(obj.id,))
        return format_html('<a href="{}">{} {}</a>',
                           url,
                           obj.created.date(),
                           obj.created.strftime('%H:%M'))


@admin.register(Funding)
class FundingAdmin(ActivityChildAdmin):
    inlines = (DonationInline,)
    base_model = Funding

    raw_id_fields = ActivityChildAdmin.raw_id_fields + ['account']

    readonly_fields = ActivityChildAdmin.readonly_fields + ['amount_raised']

    fieldsets = (
        (_('Basic'), {'fields': (
            'title', 'slug', 'initiative', 'owner', 'status', 'status_transition', 'created', 'updated'
        )}),
        (_('Details'), {'fields': (
            'description',
            'deadline', 'duration',
            'target', 'amount_raised',
            'accepted_currencies',
            'account'
        )}),
    )


@admin.register(Donation)
class DonationAdmin(FSMAdmin):
    raw_id_fields = ['activity', 'user']
    readonly_fields = ['payment_link', 'status']
    model = Donation
    list_display = ['user', 'status', 'amount']

    fields = ['created', 'activity', 'user', 'amount', 'status', 'status_transition', 'payment_link']

    def payment_link(self, obj):
        url = reverse('admin:funding_payment_change', args=(obj.payment.id,))
        return format_html('<a href="{}">{}</a>', url, obj.payment)

    payment_link.short_description = _('Payment')


class PaymentChildAdmin(PolymorphicChildModelAdmin, FSMAdmin):

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
    model = Payment
    child_models = (StripePayment, PledgePayment)
