from bluebottle.bb_payouts.admin_utils import link_to
from django.contrib.admin.templatetags.admin_static import static
from bluebottle.utils.model_dispatcher import get_donation_model, get_model_mapping
from django.contrib import admin
from django.core.urlresolvers import reverse

DONATION_MODEL = get_donation_model()
MODEL_MAP = get_model_mapping()


class DonationAdmin(admin.ModelAdmin):
    date_hierarchy = 'updated'
    list_display = ('updated', 'admin_project', 'fundraiser', 'user', 'user_full_name', 'amount', 'related_payment_method', 'status')
    list_filter = ('order__status', )
    ordering = ('-updated', )
    raw_id_fields = ('project', 'fundraiser')
    readonly_fields = ('order_link', 'created', 'updated', 'completed', 'status', 'user')
    fields = readonly_fields + ('amount', 'project', 'fundraiser')
    search_fields = ('order__user__first_name', 'order__user__last_name', 'order__user__email', 'project__title')

    def user_full_name(self, obj):
        if obj.order.user:
            return obj.order.user.full_name
        return '?'

    def user(self, obj):
        return obj.user

    def payment_method(self, obj):
        return

    def related_payment_method(self, obj):
        order_payment = obj.order.get_latest_order_payment()
        if not order_payment or not order_payment.payment:
            return '?'
        icon = static(order_payment.payment.method_icon)
        return '<img src="{0}" height="16px" title="{1}" />'.format(icon, order_payment.payment.method_name)

    related_payment_method.short_description = 'Payment method'
    related_payment_method.allow_tags = True

    def order_link(self, obj):
        object = obj.order
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>Order: {1}</a>".format(str(url), obj.id)

    order_link.allow_tags = True

    # Link to project
    admin_project = link_to(
        lambda obj: obj.project,
        'admin:{0}_{1}_change'.format(MODEL_MAP['project']['app'], MODEL_MAP['project']['class'].lower()),
        view_args=lambda obj: (obj.project.id, ),
        short_description='project',
        truncate=50
    )



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

