from bluebottle.bb_payouts.admin_utils import link_to
from bluebottle.utils.admin import export_as_csv_action, TotalAmountAdminChangeList
from bluebottle.utils.utils import StatusDefinition
from django.contrib.admin.filters import SimpleListFilter
from django.contrib.admin.templatetags.admin_static import static
from bluebottle.utils.model_dispatcher import get_donation_model, get_model_mapping, get_order_model
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Sum
from django.utils.translation import ugettext_lazy as _

DONATION_MODEL = get_donation_model()
ORDER_MODEL = get_order_model()
MODEL_MAP = get_model_mapping()


class DonationStatusFilter(SimpleListFilter):
    title = _('Status')

    parameter_name = 'status__exact'
    default_status = 'pending_or_success'

    def lookups(self, request, model_admin):
        return (('all', _('All')), ('pending_or_success', _('Pending/Success')) ) + ORDER_MODEL.STATUS_CHOICES

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else lookup == self.default_status,
                'query_string': cl.get_query_string({self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None or self.value() == 'pending_or_success':
            return queryset.filter(order__status__in=[StatusDefinition.PENDING, StatusDefinition.SUCCESS])
        elif self.value() != 'all':
            return queryset.filter(order__status=self.value())
        return queryset


class DonationUserFilter(SimpleListFilter):
    title = _('User type')

    parameter_name = 'user_type'
    default_status = 'all'

    def lookups(self, request, model_admin):
        return (('all', _('All')), ('member', _('Member')),
                ('anonymous', _('Anonymous')), ('guest', _('Guest')) )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else lookup == self.default_status,
                'query_string': cl.get_query_string({self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == 'member':
            return queryset.filter(anonymous=False, order__user__isnull=False)
        elif self.value() == 'anonymous':
            return queryset.filter(anonymous=True)
        elif self.value() == 'guest':
            return queryset.filter(order__user__isnull=True)
        return queryset


class DonationAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('created', 'completed', 'admin_project', 'fundraiser', 'user', 'user_full_name', 'amount',
                    'related_payment_method', 'order_type', 'status')
    list_filter = (DonationStatusFilter, 'order__order_type', DonationUserFilter)
    ordering = ('-created',  )
    raw_id_fields = ('project', 'fundraiser')
    readonly_fields = ('order_link', 'created', 'updated', 'completed', 'status', 'user_link', 'project_link', 'fundraiser_link')
    fields = readonly_fields + ('amount', 'project', 'fundraiser')
    search_fields = ('order__user__first_name', 'order__user__last_name', 'order__user__email', 'project__title')

    export_fields = ['project', 'order__user', 'amount', 'created', 'updated', 'completed', 'order__status',
                     'order__order_type']
    actions = (export_as_csv_action(fields=export_fields), )

    def get_changelist(self, request):
        self.total_column = 'amount'
        return TotalAmountAdminChangeList

    def user_full_name(self, obj):
        if obj.anonymous:
            return '-anonymous-'
        if obj.order.user:
            return obj.order.user.full_name
        return '-guest-'

    def user(self, obj):
        return obj.user

    def payment_method(self, obj):
        return

    def related_payment_method(self, obj):
        order_payment = obj.order.get_latest_order_payment()
        if not order_payment or not order_payment.payment:
            return '?'
        return order_payment.payment.method_name

    related_payment_method.short_description = 'Payment method'
    related_payment_method.allow_tags = True

    def order_link(self, obj):
        object = obj.order
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label, object._meta.module_name), args=[object.id])
        return "<a href='{0}'>Order: {1}</a>".format(str(url), obj.id)

    order_link.allow_tags = True

    def user_link(self, obj):
        user = obj.order.user
        url = reverse('admin:{0}_{1}_change'.format(user._meta.app_label, user._meta.module_name), args=[user.id])
        return "<a href='{0}'>{1}</a>".format(str(url), user)

    user_link.allow_tags = True

    def project_link(self, obj):
        project = obj.project
        url = reverse('admin:{0}_{1}_change'.format(project._meta.app_label, project._meta.module_name), args=[project.id])
        return "<a href='{0}'>{1}</a>".format(str(url), project)

    project_link.allow_tags = True

    def fundraiser_link(self, obj):
        fundraiser = obj.fundraiser
        url = reverse('admin:{0}_{1}_change'.format(fundraiser._meta.app_label, fundraiser._meta.module_name), args=[fundraiser.id])
        return "<a href='{0}'>{1}</a>".format(str(url), fundraiser)

    fundraiser_link.allow_tags = True

    def order_type(self, obj):
        return obj.order.order_type


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

