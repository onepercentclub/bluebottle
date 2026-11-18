from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from polymorphic.admin import PolymorphicParentModelAdmin

from bluebottle.activity_links.models import LinkedDeed, LinkedFunding, LinkedDateActivity, LinkedActivity, \
    LinkedDateSlot, LinkedCollectCampaign, LinkedDeadlineActivity, LinkedPeriodicActivity, LinkedScheduleActivity, \
    LinkedGrantApplication
from bluebottle.fsm.admin import StateMachineAdminMixin
from bluebottle.fsm.forms import StateMachineModelForm


def get_address(location):
    if not location:
        return '-'
    return location.formatted_address or str(location)


def get_slot_addresses(activity):
    addresses = []
    for slot in activity.slots.select_related('location'):
        address = get_address(slot.location)
        if address not in addresses:
            addresses.append(address)
    return ', '.join(addresses) or '-'


class LinkedBaseAdmin(StateMachineAdminMixin, admin.ModelAdmin):
    form = StateMachineModelForm
    readonly_fields = ["title", "link", "status", "host_organization"]
    fields = readonly_fields + ['archived']
    superadmin_fields = ['force_status']

    def get_fieldsets(self, request, obj):
        fieldsets = (
            (_('Details'), {'fields': self.get_fields(request, obj)}),
        )
        if request.user.is_superuser:
            fieldsets += (
                (_('Super admin'), {'fields': self.superadmin_fields}),
            )
        return fieldsets


class LinkedLocationAdminMixin:
    @admin.display(description=_('Address'))
    def address(self, obj):
        return get_address(obj.location)


@admin.register(LinkedDeed)
class LinkedDeedAdmin(LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end']
    fields = readonly_fields + ['archived']


@admin.register(LinkedCollectCampaign)
class LinkedCollectCampaignAdmin(LinkedLocationAdminMixin, LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'collect_type', 'location', 'address']
    fields = readonly_fields + ['archived']


@admin.register(LinkedFunding)
class LinkedFundingAdmin(LinkedLocationAdminMixin, LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'target', 'donated', 'location', 'address']
    fields = readonly_fields + ['archived']


@admin.register(LinkedGrantApplication)
class LinkedGrantApplicationAdmin(LinkedLocationAdminMixin, LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'target', 'location', 'address']
    fields = readonly_fields


class LinkedDateSlotInline(admin.TabularInline):
    model = LinkedDateSlot
    extra = 0
    fields = ['start', 'end', 'location', 'address']
    readonly_fields = ['address']

    @admin.display(description=_('Address'))
    def address(self, obj):
        return get_address(obj.location)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class UsedHostOrganizationListFilter(admin.SimpleListFilter):
    title = 'host organization'
    parameter_name = 'host_organization'

    def lookups(self, request, model_admin):
        queryset = model_admin.get_queryset(request)
        organization_ids = queryset.exclude(
            host_organization__isnull=True
        ).values_list('host_organization_id', flat=True).distinct()

        organization_model = model_admin.model._meta.get_field(
            'host_organization'
        ).remote_field.model

        organizations = organization_model.objects.filter(
            pk__in=organization_ids
        ).order_by('name')

        return [(str(organization.pk), str(organization)) for organization in organizations]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(host_organization_id=self.value())
        return queryset


@admin.register(LinkedDateActivity)
class LinkedDateActivityAdmin(LinkedBaseAdmin):
    inlines = [LinkedDateSlotInline]
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['address']
    fields = readonly_fields + ['archived']

    @admin.display(description=_('Address'))
    def address(self, obj):
        return get_slot_addresses(obj)


@admin.register(LinkedDeadlineActivity)
class LinkedDeadlineActivityAdmin(LinkedLocationAdminMixin, LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'duration', 'location', 'address']
    fields = readonly_fields + ['archived']


@admin.register(LinkedPeriodicActivity)
class LinkedPeriodicActivityAdmin(LinkedLocationAdminMixin, LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'duration', 'period', 'location', 'address']
    fields = readonly_fields + ['archived']


@admin.register(LinkedScheduleActivity)
class LinkedScheduleActivityAdmin(LinkedLocationAdminMixin, LinkedBaseAdmin):
    readonly_fields = LinkedBaseAdmin.readonly_fields + ['start', 'end', 'duration', 'location', 'address']
    fields = readonly_fields + ['archived']


@admin.register(LinkedActivity)
class LinkedActivityAdmin(PolymorphicParentModelAdmin):
    base_model = LinkedActivity
    search_fields = ['title']
    list_filter = [UsedHostOrganizationListFilter, 'archived']
    child_models = (
        LinkedDeed,
        LinkedFunding,
        LinkedGrantApplication,
        LinkedDateActivity,
        LinkedPeriodicActivity,
        LinkedDeadlineActivity,
        LinkedCollectCampaign,
        LinkedScheduleActivity
    )

    polymorphic_list = True

    list_display = [
        'title', 'activity_type', 'address', 'status'
    ]

    def activity_type(self, obj):
        return obj.get_real_instance_class().activity_type

    @admin.display(description=_('Address'))
    def address(self, obj):
        if isinstance(obj, LinkedDateActivity):
            return get_slot_addresses(obj)
        return get_address(getattr(obj, 'location', None))
