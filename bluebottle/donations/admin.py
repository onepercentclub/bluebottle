from django import forms
from django.contrib.admin.filters import SimpleListFilter
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _

from bluebottle.donations.models import Donation
from bluebottle.orders.models import Order
from bluebottle.payouts.admin_utils import link_to
from bluebottle.rewards.models import Reward
from bluebottle.utils.admin import (
    export_as_csv_action, TotalAmountAdminChangeList)
from bluebottle.utils.utils import StatusDefinition


class DonationStatusFilter(SimpleListFilter):
    title = _('Status')

    parameter_name = 'status__exact'
    default_status = 'pending_or_success'

    def lookups(self, request, model_admin):
        choises = (('all', _('All')),
                   ('pending_or_success', _('Pending/Success')))
        return choises + Order.STATUS_CHOICES

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else
                lookup == self.default_status,
                'query_string': cl.get_query_string(
                    {self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is None or self.value() == 'pending_or_success':
            return queryset.filter(
                order__status__in=[StatusDefinition.PENDING,
                                   StatusDefinition.SUCCESS])
        elif self.value() != 'all':
            return queryset.filter(order__status=self.value())
        return queryset


class DonationUserFilter(SimpleListFilter):
    title = _('User type')

    parameter_name = 'user_type'
    default_status = 'all'

    def lookups(self, request, model_admin):
        return (('all', _('All')), ('member', _('Member')),
                ('anonymous', _('Anonymous')), ('guest', _('Guest')))

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup if self.value() else
                lookup == self.default_status,
                'query_string': cl.get_query_string(
                    {self.parameter_name: lookup}, []),
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


class DonationAdminForm(forms.ModelForm):
    class Meta:
        model = Donation
        exclude = ()

    def __init__(self, *args, **kwargs):
        super(DonationAdminForm, self).__init__(*args, **kwargs)
        if self.instance:
            if self.instance.id:
                # You can only select a reward if the project is set on the donation
                self.fields['reward'].queryset = Reward.objects.filter(project=self.instance.project)
            else:
                self.fields['reward'].queryset = Reward.objects.none()


class DonationAdmin(admin.ModelAdmin):
    form = DonationAdminForm
    date_hierarchy = 'created'
    list_display = ('created', 'completed', 'admin_project', 'fundraiser',
                    'user', 'user_full_name', 'amount',
                    'related_payment_method', 'order_type', 'status')
    list_filter = (DonationStatusFilter, 'order__order_type',
                   DonationUserFilter)
    ordering = ('-created',)
    raw_id_fields = ('project', 'fundraiser')
    readonly_fields = ('order_link', 'created', 'updated', 'completed',
                       'status', 'user_link', 'project_link',
                       'fundraiser_link')
    fields = readonly_fields + ('amount', 'project', 'fundraiser', 'reward', 'name')
    search_fields = ('order__user__first_name', 'order__user__last_name',
                     'order__user__email', 'project__title', 'name')

    export_fields = [
        ('project', 'project'),
        ('order__user', 'user'),
        ('order__user__full_name', 'name'),
        ('order__user__remote_id', 'remote id'),
        ('name', 'name on donation'),
        ('fundraiser', 'fundraiser'),
        ('amount', 'amount'),
        ('created', 'created'),
        ('updated', 'updated'),
        ('completed', 'completed'),
        ('order__status', 'status'),
        ('order__order_type', 'type')
    ]

    actions = (export_as_csv_action(fields=export_fields),)

    def get_changelist(self, request, **kwargs):
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
        if order_payment and order_payment.status == StatusDefinition.PLEDGED:
            return 'pledge'
        if not order_payment or not order_payment.payment:
            return '?'
        return order_payment.payment.method_name

    related_payment_method.short_description = 'Payment method'

    def order_link(self, obj):
        object = obj.order
        url = reverse('admin:{0}_{1}_change'.format(object._meta.app_label,
                                                    object._meta.model_name),
                      args=[object.id])
        return format_html(
            u"<a href='{}'>Order: {}</a>",
            str(url),
            obj.id
        )

    def user_link(self, obj):
        user = obj.order.user
        url = reverse('admin:{0}_{1}_change'.format(user._meta.app_label,
                                                    user._meta.model_name),
                      args=[user.id])
        return format_html(
            u"<a href='{}'>{}</a>",
            str(url),
            user
        )

    def project_link(self, obj):
        project = obj.project
        url = reverse('admin:{0}_{1}_change'.format(project._meta.app_label,
                                                    project._meta.model_name),
                      args=[project.id])
        return format_html(
            u"<a href='{}'>{}</a>",
            str(url),
            project
        )

    def fundraiser_link(self, obj):
        fundraiser = obj.fundraiser
        url = reverse(
            'admin:{0}_{1}_change'.format(fundraiser._meta.app_label,
                                          fundraiser._meta.model_name),
            args=[fundraiser.id])
        return format_html(
            u"<a href='{}'>{}</a>",
            str(url),
            fundraiser
        )

    def order_type(self, obj):
        return obj.order.order_type

    # Link to project
    admin_project = link_to(
        lambda obj: obj.project,
        'admin:projects_project_change',
        view_args=lambda obj: (obj.project.id,),
        short_description='project',
        truncate=50
    )


admin.site.register(Donation, DonationAdmin)


class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0
    can_delete = False

    readonly_fields = ('donation_link', 'amount', 'project', 'status',
                       'user', 'fundraiser')
    fields = readonly_fields

    def has_add_permission(self, request):
        return False

    def donation_link(self, obj):
        object = obj
        url = reverse('admin:{0}_{1}_change'.format(
            object._meta.app_label, object._meta.model_name), args=[object.id])

        return format_html(
            u"<a href='{}'>Donation: {}</a>",
            str(url),
            obj.id
        )
