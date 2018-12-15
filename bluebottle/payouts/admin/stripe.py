from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payouts.models import PayoutAccount, StripePayoutAccount


class StripePayoutAccountAdmin(PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = StripePayoutAccount
    raw_id_fields = ('user', )
    readonly_fields = ('reviewed_stripe', 'account', 'project_links',
                       'bank_details', 'account_details', 'verification')

    fields = ('user', 'account_id') + readonly_fields

    def reviewed_stripe(self, obj):
        return obj.reviewed
    reviewed_stripe.short_dxescription = _('Verified')
    reviewed_stripe.description = _('Wether the account is verified and approved by Stripe.')

    def project_links(self, obj):
        return format_html(", ".join([
            "<a href='{}'>{}</a>".format(
                reverse('admin:projects_project_change', args=(p.id, )), p.id
            ) for p in obj.projects
        ]))
    project_links.short_dxescription = _('Projects')


admin.site.register(StripePayoutAccount, StripePayoutAccountAdmin)
