from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payouts.models import PayoutAccount
from bluebottle.payouts.models.stripe import StripePayoutAccount


class StripePayoutAccountAdmin(PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = StripePayoutAccount
    raw_id_fields = ('user', )


admin.site.register(StripePayoutAccount, StripePayoutAccountAdmin)
