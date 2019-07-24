from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelAdmin

from bluebottle.funding_lipisha.models import LipishaPayoutAccount
from bluebottle.payouts.admin.utils import PayoutAccountProjectLinkMixin
from bluebottle.payouts.models import PayoutAccount


@admin.register(LipishaPayoutAccount)
class LipishaPayoutAccountAdmin(PayoutAccountProjectLinkMixin, PolymorphicChildModelAdmin):
    base_model = PayoutAccount
    model = LipishaPayoutAccount
    raw_id_fields = ('user', )
    fields = ('user', 'account_number')
