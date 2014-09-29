import re
from bluebottle.payments.models import OrderPayment
from bluebottle.utils.model_dispatcher import get_donation_model
from django.contrib import admin
from django.core.urlresolvers import reverse

DONATION_MODEL = get_donation_model()

class DonationAdmin(admin.ModelAdmin):
    date_hierarchy = 'updated'
    list_display = ('updated', 'project', 'user', 'user_full_name', 'amount', 'related_payment_method', 'status')
    list_filter = ('order__status', )
    ordering = ('-updated', )
    raw_id_fields = ('project', 'fundraiser')
    readonly_fields = ('order_link', 'created', 'updated', 'status', 'user')
    fields = readonly_fields + ('amount', 'project', 'fundraiser')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'project__title')

    def user_full_name(self, obj):
        return obj.order.user.full_name

    def user(self, obj):
        return obj.user

    def payment_method(self, obj):
        return

    def related_payment_method(self, obj):
        try:
            order_payment = OrderPayment.objects.get(order=obj.order)
        except:
            return
        provider_and_method = order_payment.payment_method
        split_list = [x for x in re.split(r'([A-Z][a-z]*)', provider_and_method) if x]

        provider = split_list[0]
        method = 'none'
        if len(split_list) > 1:
            method = split_list[1]
        return '{0} - {1}'.format(provider.capitalize(), method)

    user_full_name.short_description = 'Employee name'
    user.short_description = 'Employee email address'
    related_payment_method.short_description = 'Payment Provider and Method'


    def order_link(self, obj):
        object = obj.order
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>Order: {1}</a>".format(str(url), obj.id)

    order_link.allow_tags = True

admin.site.register(DONATION_MODEL, DonationAdmin)


class DonationInline(admin.TabularInline):
    model = DONATION_MODEL
    extra = 0
    can_delete = False

    readonly_fields = ('donation_link', 'amount', 'project', 'status', 'user', 'fundraiser')
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    def donation_link(self, obj):
        object = obj
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>Donation: {1}</a>".format(str(url), obj.id)

    donation_link.allow_tags = True

