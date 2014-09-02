from bluebottle.bb_donations.admin import DonationInline
from bluebottle.orders.models import Order
from bluebottle.payments.admin import OrderPaymentInline
from django.contrib import admin


class OrderAdmin(admin.ModelAdmin):
    model = Order
    list_display = ('id', 'created', 'closed', 'total', 'status', 'user')
    list_filter = ('status', )
    raw_id_fields = ('user', )
    readonly_fields = ('total', )
    fields = readonly_fields + ('user', 'status')
    inlines = (DonationInline, OrderPaymentInline, )

admin.site.register(Order, OrderAdmin)