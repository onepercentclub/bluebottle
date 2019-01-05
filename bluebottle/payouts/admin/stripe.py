from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payouts.models import PayoutAccount, StripePayoutAccount


class StripePayoutAccountAdmin(PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = StripePayoutAccount
    raw_id_fields = ('user', )
    readonly_fields = ('reviewed_stripe', 'missing', 'project_links', 'details')

    fields = ('user', 'account_id') + readonly_fields

    def get_urls(self):
        urls = super(StripePayoutAccountAdmin, self).get_urls()
        custom_urls = [
            url(
                r'^(?P<account_id>.+)/check_status/$',
                self.admin_site.admin_view(self.check_status),
                name='stripe-payout-account-check',
            ),
        ]
        return custom_urls + urls

    def check_status(self, request, account_id):
        account = StripePayoutAccount.objects.get(id=account_id)
        account.check_status()
        payout_url = reverse('admin:payouts_payoutaccount_change', args=(account_id,))
        return HttpResponseRedirect(payout_url)

    check_status.short_description = _('Check status at Stripe')

    def details(self, obj):
        return format_html("<br/>".join([
            "<b>{}</b>: {}".format(key, value) for key, value in obj.short_details.items()
        ]))
    details.short_description = _('Account details')

    def reviewed_stripe(self, obj):
        return obj.reviewed
    reviewed_stripe.short_description = _('Verified by Stripe')

    def project_links(self, obj):
        return format_html(", ".join([
            "<a href='{}'>{}</a>".format(
                reverse('admin:projects_project_change', args=(p.id, )), p.title
            ) for p in obj.projects
        ]))
    project_links.short_description = _('Projects')

    def missing(self, obj):
        return format_html("<br/>".join(obj.fields_needed))
    missing.short_description = _('Fields still needed')


admin.site.register(StripePayoutAccount, StripePayoutAccountAdmin)
