from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payouts.models import PayoutAccount, StripePayoutAccount


class StripePayoutAccountAdmin(PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = StripePayoutAccount
    raw_id_fields = ('user', )
    readonly_fields = ('reviewed_stripe', 'account',
                       'bank_details', 'account_details', 'verification')

    fields = ('user', 'account_id') + readonly_fields

    def reviewed_stripe(self, obj):
        return obj.reviewed
    reviewed_stripe.short_description = _('Verified')
    reviewed_stripe.description = _('Wether the account is verified and approved by Stripe.')


admin.site.register(StripePayoutAccount, StripePayoutAccountAdmin)
