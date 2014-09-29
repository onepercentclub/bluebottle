from bluebottle.bb_donations.admin import DonationInline
from bluebottle.payments.admin import OrderPaymentInline
from django.contrib import admin
from django.core.urlresolvers import reverse
from bluebottle.payments.models import OrderPayment
from bluebottle.utils.model_dispatcher import get_order_model, get_donation_model

ORDER_MODEL = get_order_model()
DONATION_MODEL = get_donation_model()


class BaseOrderAdmin(admin.ModelAdmin):
    model = get_order_model()
    list_display = ('created', 'updated', 'closed', 'user', 'status', 'total')

    inlines = (DonationInline, OrderPaymentInline)

    raw_id_fields = ('user', )
    readonly_fields = ('status', 'total')

admin.site.register(ORDER_MODEL, BaseOrderAdmin)

