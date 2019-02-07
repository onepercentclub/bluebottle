import logging

from django.contrib import admin
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic.admin.parentadmin import PolymorphicParentModelAdmin

from bluebottle.payouts.admin.plain import PlainPayoutAccountAdmin
from bluebottle.payouts.admin.stripe import StripePayoutAccountAdmin
from bluebottle.payouts.admin.utils import PayoutAccountProjectLinkMixin
from bluebottle.payouts.models import PayoutAccount

logger = logging.getLogger(__name__)


class PayoutAccountAdmin(PayoutAccountProjectLinkMixin, PolymorphicParentModelAdmin):
    base_model = PayoutAccount
    list_display = ('created', 'polymorphic_ctype', 'reviewed', 'project_links')
    list_filter = ('reviewed', PolymorphicChildModelFilter)
    raw_id_fields = ('user', )

    ordering = ('-created',)

    def get_child_models(self):
        return tuple(
            (admin.model, admin) for admin in (
                StripePayoutAccountAdmin,
                PlainPayoutAccountAdmin
            )
        )


admin.site.register(PayoutAccount, PayoutAccountAdmin)
