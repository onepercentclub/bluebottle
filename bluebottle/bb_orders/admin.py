from django.contrib import admin
from django.core.urlresolvers import reverse
from bluebottle.payments.models import OrderPayment
from bluebottle.utils.model_dispatcher import get_order_model, get_donation_model

ORDER_MODEL = get_order_model()
DONATION_MODEL = get_donation_model()


class BaseOrderAdmin(admin.ModelAdmin):
    model = get_order_model()
    list_display = ('created', 'updated', 'closed', 'user', 'status', 'total', 'order_payment', 'donation')

    def order_payment(self, obj):
        order_payment = OrderPayment.objects.get(order=obj.id)
        url = reverse('admin:{0}_{1}_change'.format(order_payment._meta.app_label, order_payment._meta.module_name), args=[order_payment.id])
        return "<a href='{0}'>{1}</a>".format(str(url), order_payment.id)

    order_payment.short_description = "OrderPayment Id"
    order_payment.allow_tags = True

    def donation(self, obj):
        donation = DONATION_MODEL.objects.get(order=obj.id)
        url = reverse('admin:{0}_{1}_change'.format(donation._meta.app_label, donation._meta.module_name), args=[donation.id])
        return "<a href='{0}'>{1}</a>".format(str(url), donation.id)

    donation.short_description = "Donation Id"
    donation.allow_tags = True
    
# if you want to display more fields, unregister the model first, define a new admin class
# (possibly inheriting from BaseProjectAdmin), and then re-register it
admin.site.register(ORDER_MODEL, BaseOrderAdmin)

