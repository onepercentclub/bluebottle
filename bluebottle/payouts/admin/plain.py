from django.contrib import admin

from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.payouts.models import PayoutAccount
from bluebottle.payouts.models.plain import PlainPayoutAccount


class PlainPayoutAccountAdmin(PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = PlainPayoutAccount
    raw_id_fields = ('user', )


admin.site.register(PlainPayoutAccount, PlainPayoutAccountAdmin)
