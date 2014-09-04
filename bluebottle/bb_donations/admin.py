from bluebottle.utils.model_dispatcher import get_donation_model
from django.contrib import admin
from django.core.urlresolvers import reverse

DONATION_MODEL = get_donation_model()


class DonationAdmin(admin.ModelAdmin):
    date_hierarchy = 'updated'
    list_display = ('updated', 'project', 'user', 'amount', 'status')
    list_filter = ('order__status', )
    ordering = ('-updated', )
    raw_id_fields = ('project', 'fundraiser')
    readonly_fields = ('order_link', 'created', 'updated', 'status', 'user')
    fields = readonly_fields + ('amount', 'project', 'fundraiser')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'project__title')

    def order_link(self, obj):
        object = obj.order
        print object._meta.app_label
        print object._meta.module_name
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        print url
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
        print object._meta.app_label
        print object._meta.module_name
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        print url
        return "<a href='{0}'>Donation: {1}</a>".format(str(url), obj.id)

    donation_link.allow_tags = True

