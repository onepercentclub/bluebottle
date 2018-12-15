from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payouts.models import PayoutAccount, StripePayoutAccount


class StripePayoutAccountAdmin(PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = StripePayoutAccount
    raw_id_fields = ('user', )
    readonly_fields = ('account', )


admin.site.register(StripePayoutAccount, StripePayoutAccountAdmin)
